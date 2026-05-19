# Thumbnail Generator Lambda

## Overview

**Purpose:** Generate video thumbnails from workout recordings.  
**Runtime:** Python 3.12  
**Trigger:** S3 ObjectCreated notification or SQS queue

## Features

- Generates thumbnails from workout videos
- Supports S3 event triggers and SQS messages
- Mock implementation (returns placeholder image)
- Saves thumbnails to S3 with caching headers
- Production-ready structure for ffmpeg/opencv integration

## Environment Variables

```bash
AWS_REGION=ap-northeast-2
S3_BUCKET=gympt-videos
THUMBNAIL_WIDTH=320
THUMBNAIL_HEIGHT=180
THUMBNAIL_QUALITY=85
```

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test with example event
python -c "
import json
from handler import lambda_handler

with open('event.example.json') as f:
    event = json.load(f)

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

## Event Formats

### SQS Message

```json
{
  "Records": [
    {
      "body": "{\"sessionId\": \"session-abc\", \"videoKey\": \"videos/user-123/workout.mp4\", \"bucket\": \"gympt-videos\"}"
    }
  ]
}
```

### S3 Event

```json
{
  "Records": [
    {
      "s3": {
        "bucket": {"name": "gympt-videos"},
        "object": {"key": "videos/user-123/workout.mp4"}
      }
    }
  ]
}
```

## S3 Key Structure

**Input:** `videos/{userId}/{sessionId}/workout.mp4`  
**Output:** `thumbnails/{userId}/{sessionId}/workout.jpg`

## Production Implementation

For actual video thumbnail extraction, replace `generate_thumbnail_from_video()` with:

```python
import cv2

def generate_thumbnail_from_video(bucket: str, key: str) -> BytesIO:
    # Download video from S3
    video_obj = s3_client.get_object(Bucket=bucket, Key=key)
    
    # Save to temp file
    temp_path = f"/tmp/{os.path.basename(key)}"
    with open(temp_path, 'wb') as f:
        f.write(video_obj['Body'].read())
    
    # Extract frame at 1 second
    cap = cv2.VideoCapture(temp_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
    success, frame = cap.read()
    cap.release()
    
    if not success:
        raise Exception("Could not extract frame")
    
    # Resize and convert
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    
    # Return as JPEG
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=THUMBNAIL_QUALITY)
    buffer.seek(0)
    return buffer
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 60 seconds
- **Memory:** 1024 MB (for video processing)
- **Ephemeral Storage:** 2048 MB (for video download)
- **IAM:** S3 read/write

For production with opencv:
- Use Lambda Layer with opencv-python-headless and ffmpeg

## Testing

```bash
pytest tests/ -v
```
