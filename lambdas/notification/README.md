# Notification Lambda

## Overview

**Purpose:** Multi-channel notification dispatcher (Slack, Email, Push).  
**Runtime:** Python 3.12  
**Trigger:** SQS queue (notification-queue)

## Features

- Multi-channel support (Slack, Email, Push)
- Structured logging for local development
- Extensible notification types
- Toggle channels via environment variables
- SNS integration for email/push

## Supported Notification Types

- `REPORT_READY` - Workout report completed
- `RECOMMENDATION_UPDATE` - Intensity adjustment
- `WORKOUT_COMPLETED` - Workout session finished
- `POSTURE_ALERT` - Form issue detected
- `GOAL_ACHIEVED` - Fitness goal reached

## Environment Variables

```bash
AWS_REGION=ap-northeast-2
ENABLE_SLACK=false
ENABLE_EMAIL=false
ENABLE_PUSH=false
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SNS_TOPIC_ARN=arn:aws:sns:ap-northeast-2:123456789012:gympt-notifications
```

## Local Testing

In local development, all notifications are logged to console.

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

## SQS Message Formats

### Report Ready

```json
{
  "type": "REPORT_READY",
  "userId": "user-123",
  "reportUrl": "s3://gympt-reports/user-123/report.json",
  "period": "weekly",
  "timestamp": "2024-05-18T10:00:00Z"
}
```

### Recommendation Update

```json
{
  "type": "RECOMMENDATION_UPDATE",
  "userId": "user-123",
  "adjustment": "INCREASE",
  "timestamp": "2024-05-18T10:00:00Z"
}
```

### Workout Completed

```json
{
  "type": "WORKOUT_COMPLETED",
  "userId": "user-123",
  "sessionId": "session-abc",
  "score": 8.5,
  "timestamp": "2024-05-18T10:00:00Z"
}
```

### Posture Alert

```json
{
  "type": "POSTURE_ALERT",
  "userId": "user-123",
  "sessionId": "session-abc",
  "issueType": "knee_valgus",
  "severity": "high",
  "timestamp": "2024-05-18T10:00:00Z"
}
```

## Channel Implementation

### Slack

Uses incoming webhooks. Configure webhook URL in environment.

Create webhook at: https://api.slack.com/messaging/webhooks

### Email

Uses SNS topic with email subscriptions.

Setup:
```bash
aws sns create-topic --name gympt-notifications --region ap-northeast-2
aws sns subscribe --topic-arn arn:aws:sns:ap-northeast-2:123456789012:gympt-notifications \
  --protocol email --notification-endpoint user@example.com
```

### Push (Mobile)

Mock implementation. Production requires:

1. Create SNS Platform Application (FCM/APNS)
2. Store device tokens in DynamoDB
3. Send to platform-specific endpoints

```python
# Production push example
sns_client.publish(
    TargetArn="arn:aws:sns:ap-northeast-2:123456789012:endpoint/GCM/GymPT/device-token",
    Message=json.dumps({
        "GCM": json.dumps({
            "notification": {
                "title": "Workout Report Ready",
                "body": "Your weekly report is available"
            }
        })
    }),
    MessageStructure='json'
)
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **IAM:** SNS publish

Environment-specific settings:
- **Local:** All channels disabled, logs only
- **Dev:** Slack enabled for debugging
- **Prod:** All channels enabled

## Testing

```bash
pytest tests/ -v
```
