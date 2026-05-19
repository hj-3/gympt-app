# Report Generator Lambda

## Overview

**Purpose:** Generate workout performance reports with AI insights.  
**Runtime:** Python 3.12  
**Trigger:** SQS queue (report-generation-queue)

## Features

- Fetches workout sessions and posture events from DynamoDB
- Calculates aggregate metrics (total sessions, calories, average score)
- Generates insights using Bedrock Claude (or mock mode)
- Saves report JSON to S3
- Publishes notification to SQS

## Environment Variables

```bash
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
S3_BUCKET=gympt-reports
NOTIFICATION_QUEUE_URL=https://sqs.ap-northeast-2.amazonaws.com/123456789012/notification-queue
ENABLE_BEDROCK_MOCK=true
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
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

## SQS Message Format

```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "period": "weekly",
  "requestedAt": "2024-05-18T10:00:00Z"
}
```

## Report Structure

```json
{
  "userId": "uuid",
  "period": "weekly",
  "startDate": "2024-05-11T10:00:00Z",
  "endDate": "2024-05-18T10:00:00Z",
  "metrics": {
    "totalSessions": 5,
    "totalDuration": 1800,
    "totalCalories": 450,
    "averageScore": 8.2,
    "exerciseBreakdown": {"Squat": 3, "Pushup": 2},
    "commonIssues": [["knee_valgus", 5], ["depth", 3]]
  },
  "insights": "AI-generated insights...",
  "generatedAt": "2024-05-18T10:00:00Z"
}
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 60 seconds
- **Memory:** 512 MB
- **IAM:** DynamoDB read, S3 write, SQS send, Bedrock invoke

## Testing

```bash
pytest tests/ -v
```
