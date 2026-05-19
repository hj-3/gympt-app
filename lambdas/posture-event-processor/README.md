# Posture Event Processor Lambda

## Overview

**Purpose:** Process and enrich posture analysis events from real-time analysis.  
**Runtime:** Python 3.12  
**Trigger:** SQS queue (posture-event-queue)

## Features

- Enriches posture events with calculated metrics
- Aggregates issues by type and severity
- Calculates overall quality score
- Saves enriched events to DynamoDB
- Publishes CloudWatch custom metrics

## Environment Variables

```bash
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
CLOUDWATCH_NAMESPACE=GymPT/PostureAnalysis
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
  "sessionId": "session-abc",
  "userId": "user-123",
  "eventId": "evt-001",
  "timestamp": "2024-05-18T10:30:00Z",
  "analysis": {
    "score": 8.0,
    "issues": [
      {
        "type": "knee_valgus",
        "severity": "medium",
        "correction": "Push knees outward"
      }
    ]
  }
}
```

## Enriched Event Structure

```json
{
  "sessionId": "session-abc",
  "userId": "user-123",
  "analysis": {...},
  "enrichedMetrics": {
    "overallScore": 7.0,
    "quality": "GOOD",
    "issueAggregation": {
      "typeBreakdown": {"knee_valgus": 1},
      "severityBreakdown": {"medium": 1},
      "totalIssues": 1
    }
  },
  "processedAt": "2024-05-18T10:30:05Z"
}
```

## CloudWatch Metrics

Published to namespace `GymPT/PostureAnalysis`:

- **PostureScore** - Overall form score (0-10)
- **IssueCount** - Total number of issues detected
- **Issues_Urgent** - Count of urgent severity issues
- **Issues_High** - Count of high severity issues
- **Issues_Medium** - Count of medium severity issues
- **Issues_Low** - Count of low severity issues

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **IAM:** DynamoDB write, CloudWatch metrics

## Testing

```bash
pytest tests/ -v
```
