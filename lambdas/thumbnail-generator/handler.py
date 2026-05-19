import json
import logging
import os
from io import BytesIO
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

import boto3
from botocore.exceptions import ClientError
from PIL import Image

# Configure structured logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Environment variables
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "gympt-videos")
THUMBNAIL_WIDTH = int(os.getenv("THUMBNAIL_WIDTH", "320"))
THUMBNAIL_HEIGHT = int(os.getenv("THUMBNAIL_HEIGHT", "180"))
THUMBNAIL_QUALITY = int(os.getenv("THUMBNAIL_QUALITY", "85"))

# AWS clients
s3_client = boto3.client("s3", region_name=AWS_REGION)


def generate_mock_thumbnail(width: int, height: int) -> BytesIO:
    """Generate a mock thumbnail image."""
    # Create a simple gradient image as placeholder
    img = Image.new("RGB", (width, height), color="lightblue")

    # Add text overlay
    try:
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(img)
        text = "Workout\nThumbnail"

        # Use default font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        draw.text((x, y), text, fill="white", font=font)
    except Exception as e:
        logger.warning(f"Could not add text overlay: {e}")

    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=THUMBNAIL_QUALITY)
    buffer.seek(0)

    logger.info(f"Generated mock thumbnail: {width}x{height}")
    return buffer


def generate_thumbnail_from_video(bucket: str, key: str) -> BytesIO:
    """
    Generate thumbnail from video (mock implementation).

    In production, this would:
    1. Download video from S3
    2. Extract frame at specific timestamp using ffmpeg or opencv
    3. Resize to thumbnail dimensions
    4. Return as BytesIO

    For now, returns a mock thumbnail.
    """
    logger.info(f"Generating thumbnail from s3://{bucket}/{key}")

    # TODO: Implement actual video frame extraction
    # For now, return mock thumbnail
    return generate_mock_thumbnail(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)


def save_thumbnail_to_s3(thumbnail: BytesIO, original_key: str) -> str:
    """Save thumbnail to S3 with thumbnails/ prefix."""
    try:
        # Construct thumbnail key
        # videos/user-123/session-abc/workout.mp4 -> thumbnails/user-123/session-abc/workout.jpg
        if original_key.startswith("videos/"):
            thumbnail_key = original_key.replace("videos/", "thumbnails/", 1)
        else:
            thumbnail_key = f"thumbnails/{original_key}"

        # Change extension to .jpg
        thumbnail_key = os.path.splitext(thumbnail_key)[0] + ".jpg"

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=thumbnail_key,
            Body=thumbnail.getvalue(),
            ContentType="image/jpeg",
            CacheControl="max-age=31536000",  # 1 year
        )

        s3_url = f"s3://{S3_BUCKET}/{thumbnail_key}"
        logger.info(f"Saved thumbnail to {s3_url}")

        return thumbnail_key
    except ClientError as e:
        logger.error(f"Error saving thumbnail to S3: {e}")
        raise


def process_s3_event(event: Dict[str, Any]) -> Dict[str, str]:
    """Process S3 ObjectCreated event."""
    bucket = event["s3"]["bucket"]["name"]
    key = event["s3"]["object"]["key"]

    logger.info(f"Processing S3 event: s3://{bucket}/{key}")

    # Generate thumbnail
    thumbnail = generate_thumbnail_from_video(bucket, key)

    # Save to S3
    thumbnail_key = save_thumbnail_to_s3(thumbnail, key)

    return {
        "originalKey": key,
        "thumbnailKey": thumbnail_key,
        "bucket": bucket,
    }


def process_sqs_message(message: Dict[str, Any]) -> Dict[str, str]:
    """Process SQS message with video metadata."""
    bucket = message.get("bucket", S3_BUCKET)
    key = message["videoKey"]
    session_id = message.get("sessionId")

    logger.info(f"Processing SQS message for session: {session_id}")

    # Generate thumbnail
    thumbnail = generate_thumbnail_from_video(bucket, key)

    # Save to S3
    thumbnail_key = save_thumbnail_to_s3(thumbnail, key)

    return {
        "sessionId": session_id,
        "originalKey": key,
        "thumbnailKey": thumbnail_key,
        "bucket": bucket,
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle thumbnail generation from S3 events or SQS.

    Supports two event types:
    1. S3 ObjectCreated notification
    2. SQS message with video metadata

    SQS message format:
    {
        "sessionId": "session-abc",
        "videoKey": "videos/user-123/workout.mp4",
        "bucket": "gympt-videos"
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        results = []

        # Check if this is an S3 event
        if "Records" in event:
            for record in event["Records"]:
                try:
                    # S3 event
                    if "s3" in record:
                        result = process_s3_event(record)
                        results.append(result)

                    # SQS message
                    elif "body" in record:
                        message = json.loads(record["body"])
                        result = process_sqs_message(message)
                        results.append(result)

                except Exception as e:
                    logger.error(f"Error processing record: {e}", exc_info=True)
                    continue

        logger.info(f"Successfully processed {len(results)} thumbnails")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": len(results),
                "results": results,
            }),
        }

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
