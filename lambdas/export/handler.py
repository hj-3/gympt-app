import csv
import json
import logging
import os
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Dict, List
from pythonjsonlogger import jsonlogger

import boto3
from botocore.exceptions import ClientError

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
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "gympt-local")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "gympt-exports")
PRESIGNED_URL_EXPIRY = int(os.getenv("PRESIGNED_URL_EXPIRY", "3600"))  # 1 hour

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)


def get_workout_sessions(user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch workout sessions for date range."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-workout-sessions")

        response = table.query(
            KeyConditionExpression="userId = :uid AND completedAt BETWEEN :start AND :end",
            ExpressionAttributeValues={
                ":uid": user_id,
                ":start": start_date,
                ":end": end_date,
            },
        )

        sessions = response.get("Items", [])
        logger.info(f"Retrieved {len(sessions)} workout sessions for export")
        return sessions
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return []


def get_body_profiles(user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch body profile measurements for date range."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-body-profiles")

        response = table.query(
            KeyConditionExpression="userId = :uid AND recordedAt BETWEEN :start AND :end",
            ExpressionAttributeValues={
                ":uid": user_id,
                ":start": start_date,
                ":end": end_date,
            },
        )

        profiles = response.get("Items", [])
        logger.info(f"Retrieved {len(profiles)} body profiles for export")
        return profiles
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return []


def export_to_csv(sessions: List[Dict[str, Any]], profiles: List[Dict[str, Any]]) -> str:
    """Export workout data to CSV format."""
    output = StringIO()
    writer = csv.writer(output)

    # Write workout sessions
    writer.writerow(["=== WORKOUT SESSIONS ==="])
    writer.writerow([
        "Session ID",
        "Exercise",
        "Completed At",
        "Duration (s)",
        "Calories",
        "Average Score",
        "Status",
    ])

    for session in sessions:
        writer.writerow([
            session.get("sessionId", ""),
            session.get("exerciseName", ""),
            session.get("completedAt", ""),
            session.get("duration", ""),
            session.get("caloriesBurned", ""),
            session.get("averageScore", ""),
            session.get("status", ""),
        ])

    # Write body profiles
    writer.writerow([])
    writer.writerow(["=== BODY MEASUREMENTS ==="])
    writer.writerow([
        "Recorded At",
        "Weight (kg)",
        "Height (cm)",
        "BMI",
        "Body Fat %",
        "Muscle Mass (kg)",
    ])

    for profile in profiles:
        writer.writerow([
            profile.get("recordedAt", ""),
            profile.get("weight", ""),
            profile.get("height", ""),
            profile.get("bmi", ""),
            profile.get("bodyFat", ""),
            profile.get("muscleMass", ""),
        ])

    csv_content = output.getvalue()
    output.close()

    logger.info(f"Generated CSV with {len(sessions)} sessions and {len(profiles)} profiles")
    return csv_content


def export_to_json(sessions: List[Dict[str, Any]], profiles: List[Dict[str, Any]]) -> str:
    """Export workout data to JSON format."""
    data = {
        "exportedAt": datetime.utcnow().isoformat(),
        "workoutSessions": sessions,
        "bodyProfiles": profiles,
        "summary": {
            "totalSessions": len(sessions),
            "totalProfiles": len(profiles),
        },
    }

    json_content = json.dumps(data, indent=2, default=str)
    logger.info(f"Generated JSON with {len(sessions)} sessions and {len(profiles)} profiles")
    return json_content


def upload_to_s3(content: str, user_id: str, format: str) -> str:
    """Upload export file to S3."""
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        key = f"exports/{user_id}/{timestamp}_export.{format}"

        content_type = "application/json" if format == "json" else "text/csv"

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )

        logger.info(f"Uploaded export to s3://{S3_BUCKET}/{key}")
        return key
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        raise


def generate_presigned_url(key: str) -> str:
    """Generate pre-signed URL for download."""
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=PRESIGNED_URL_EXPIRY,
        )

        logger.info(f"Generated pre-signed URL for {key}")
        return url
    except ClientError as e:
        logger.error(f"Pre-signed URL generation error: {e}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Export user workout data to CSV or JSON.

    Can be invoked directly or via SQS.

    Direct invocation:
    {
        "userId": "user-uuid",
        "format": "csv|json",
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-12-31T23:59:59Z"
    }

    SQS message format: same as above
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Parse event (direct or SQS)
        if "Records" in event:
            message = json.loads(event["Records"][0]["body"])
        else:
            message = event

        user_id = message["userId"]
        format = message.get("format", "json").lower()
        start_date = message.get("startDate")
        end_date = message.get("endDate")

        # Default date range: last 30 days
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        if not start_date:
            start = datetime.utcnow() - timedelta(days=30)
            start_date = start.isoformat()

        logger.info(f"Exporting data for user {user_id} from {start_date} to {end_date}")

        # Fetch data
        sessions = get_workout_sessions(user_id, start_date, end_date)
        profiles = get_body_profiles(user_id, start_date, end_date)

        if not sessions and not profiles:
            logger.warning(f"No data found for user: {user_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "No data found for export"}),
            }

        # Generate export
        if format == "csv":
            content = export_to_csv(sessions, profiles)
        else:
            content = export_to_json(sessions, profiles)

        # Upload to S3
        s3_key = upload_to_s3(content, user_id, format)

        # Generate pre-signed URL
        download_url = generate_presigned_url(s3_key)

        result = {
            "userId": user_id,
            "format": format,
            "s3Key": s3_key,
            "downloadUrl": download_url,
            "expiresIn": PRESIGNED_URL_EXPIRY,
            "recordCount": {
                "workoutSessions": len(sessions),
                "bodyProfiles": len(profiles),
            },
            "exportedAt": datetime.utcnow().isoformat(),
        }

        logger.info(f"Export completed for user: {user_id}")

        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }

    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing required field: {e}"}),
        }
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
