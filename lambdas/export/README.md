# Export Lambda

## Overview

**Purpose:** Export user workout data to CSV or JSON with pre-signed URLs.  
**Runtime:** Python 3.12  
**Trigger:** Direct invocation, API Gateway, or SQS queue

## Features

- Export workout sessions and body profiles
- CSV and JSON format support
- S3 storage with organized prefixes
- Pre-signed URL generation for secure downloads
- Configurable date range (default: 30 days)
- Expires URLs after 1 hour (configurable)

## Environment Variables

```bash
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
S3_BUCKET=gympt-exports
PRESIGNED_URL_EXPIRY=3600
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

## Invocation Formats

### Direct Invocation

```json
{
  "userId": "user-123",
  "format": "json",
  "startDate": "2024-01-01T00:00:00Z",
  "endDate": "2024-05-18T23:59:59Z"
}
```

### Via API Gateway

```bash
curl -X POST https://api.gympt.com/api/v1/exports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-123",
    "format": "csv"
  }'
```

### Via SQS

```json
{
  "Records": [
    {
      "body": "{\"userId\": \"user-123\", \"format\": \"json\"}"
    }
  ]
}
```

## Response Format

```json
{
  "userId": "user-123",
  "format": "json",
  "s3Key": "exports/user-123/20240518_103000_export.json",
  "downloadUrl": "https://gympt-exports.s3.amazonaws.com/exports/user-123/...",
  "expiresIn": 3600,
  "recordCount": {
    "workoutSessions": 42,
    "bodyProfiles": 10
  },
  "exportedAt": "2024-05-18T10:30:00Z"
}
```

## CSV Format

```csv
=== WORKOUT SESSIONS ===
Session ID,Exercise,Completed At,Duration (s),Calories,Average Score,Status
session-1,Squat,2024-05-15T10:00:00Z,300,50,8.5,COMPLETED
session-2,Pushup,2024-05-16T10:00:00Z,200,30,9.0,COMPLETED

=== BODY MEASUREMENTS ===
Recorded At,Weight (kg),Height (cm),BMI,Body Fat %,Muscle Mass (kg)
2024-05-15T00:00:00Z,70.5,175,23.0,15.2,55.0
```

## JSON Format

```json
{
  "exportedAt": "2024-05-18T10:30:00Z",
  "workoutSessions": [
    {
      "sessionId": "session-1",
      "exerciseName": "Squat",
      "completedAt": "2024-05-15T10:00:00Z",
      "duration": 300,
      "caloriesBurned": 50,
      "averageScore": 8.5,
      "status": "COMPLETED"
    }
  ],
  "bodyProfiles": [
    {
      "recordedAt": "2024-05-15T00:00:00Z",
      "weight": 70.5,
      "height": 175,
      "bmi": 23.0,
      "bodyFat": 15.2,
      "muscleMass": 55.0
    }
  ],
  "summary": {
    "totalSessions": 1,
    "totalProfiles": 1
  }
}
```

## S3 Structure

```
s3://gympt-exports/
└── exports/
    └── user-123/
        ├── 20240518_103000_export.json
        ├── 20240517_150000_export.csv
        └── ...
```

## Use Cases

1. **User Data Export** - GDPR compliance, data portability
2. **External Analysis** - Import into Excel, Google Sheets
3. **Backup** - Personal workout history backup
4. **Integration** - Third-party fitness apps

## Security

- Pre-signed URLs expire after 1 hour
- S3 bucket should have:
  - Private ACL
  - Encryption at rest (AES-256)
  - Lifecycle policy to delete exports after 7 days

```json
{
  "Rules": [
    {
      "Id": "DeleteOldExports",
      "Status": "Enabled",
      "Prefix": "exports/",
      "Expiration": {
        "Days": 7
      }
    }
  ]
}
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 60 seconds
- **Memory:** 512 MB
- **IAM:** DynamoDB read, S3 write

API Gateway Integration:
```yaml
/api/v1/exports:
  post:
    x-amazon-apigateway-integration:
      type: aws_proxy
      uri: arn:aws:lambda:ap-northeast-2:123456789012:function:export
```

## Testing

```bash
pytest tests/ -v
```
