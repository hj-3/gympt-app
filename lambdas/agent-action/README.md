# Agent Action Lambda

## Overview

**Purpose:** Bedrock Agent Action Group handler for workout-related actions.  
**Runtime:** Python 3.12  
**Trigger:** Bedrock Agent invocation

## Functions

1. **getUserProfile** - Retrieve user profile from DynamoDB
2. **getBodyProfile** - Get latest body measurements
3. **getRecentWorkoutSessions** - Fetch recent workout history
4. **saveWorkoutRecommendation** - Store AI-generated workout plan
5. **getPostureAnalysisResult** - Aggregate posture analysis for a session
6. **createWorkoutReport** - Queue report generation request

## Environment Variables

```bash
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
BACKEND_API_URL=http://localhost:8000
REPORT_QUEUE_URL=https://sqs.ap-northeast-2.amazonaws.com/123456789012/report-generation-queue
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

## Event Format

Bedrock Agent Action Group event:

```json
{
  "actionGroup": "WorkoutActions",
  "function": "getUserProfile",
  "parameters": [
    {"name": "userId", "value": "uuid"}
  ]
}
```

## Response Format

```json
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": "WorkoutActions",
    "function": "getUserProfile",
    "functionResponse": {
      "responseBody": {
        "TEXT": {
          "body": "{\"userId\": \"...\", \"email\": \"...\"}"
        }
      }
    }
  }
}
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 30 seconds
- **Memory:** 512 MB
- **IAM:** DynamoDB read/write, SQS send

## Testing

```bash
pytest tests/ -v
```
