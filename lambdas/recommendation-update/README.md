# Recommendation Update Lambda

## Overview

**Purpose:** Adjust workout intensity based on performance analysis.  
**Runtime:** Python 3.12  
**Trigger:** EventBridge rule on workout completion or SQS queue

## Features

- Analyzes recent workout performance (5 sessions)
- Calculates intensity adjustment (INCREASE/MAINTAIN/DECREASE)
- Generates specific recommendations
- Updates Backend API via REST call
- Saves recommendation history to DynamoDB

## Logic

### Intensity Adjustment Rules

| Condition | Action |
|-----------|--------|
| Avg Score ≥ 8.5 AND Completion Rate ≥ 90% | INCREASE |
| Avg Score < 6.0 OR Completion Rate < 50% | DECREASE |
| Otherwise | MAINTAIN |

### Recommendations

**INCREASE:**
- Increase weight by 5-10%
- Add 1-2 more reps per set
- Reduce rest time between sets

**DECREASE:**
- Reduce weight by 10-15%
- Focus on form over intensity
- Increase rest time between sets
- Consider active recovery days

**MAINTAIN:**
- Maintain current intensity
- Continue focusing on form

## Environment Variables

```bash
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
BACKEND_API_URL=http://localhost:8000
BACKEND_API_KEY=secret-key
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

```json
{
  "userId": "user-123",
  "sessionId": "session-abc",
  "completed": true
}
```

## Backend API Endpoint

**POST** `/api/v1/recommendations/update`

Request:
```json
{
  "userId": "user-123",
  "adjustment": "INCREASE",
  "performanceMetrics": {
    "averageScore": 8.7,
    "completionRate": 0.95,
    "totalSessions": 5
  },
  "recommendations": [
    "Increase weight by 5-10%",
    "Add 1-2 more reps per set"
  ],
  "updatedAt": "2024-05-18T10:00:00Z"
}
```

## DynamoDB Schemas

### workout-sessions (Query)
```json
{
  "userId": "user-123",
  "completedAt": "2024-05-18T10:00:00Z",
  "averageScore": 8.5,
  "status": "COMPLETED"
}
```

### recommendation-history (Write)
```json
{
  "userId": "user-123",
  "timestamp": "2024-05-18T10:00:00Z",
  "adjustment": "INCREASE",
  "performanceMetrics": {...},
  "recommendations": [...]
}
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **IAM:** DynamoDB read/write

EventBridge Rule:
```json
{
  "source": ["gympt.workouts"],
  "detail-type": ["Workout Completed"],
  "detail": {
    "status": ["COMPLETED"]
  }
}
```

## Testing

```bash
pytest tests/ -v
```
