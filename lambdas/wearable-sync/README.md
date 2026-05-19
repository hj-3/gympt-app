# Wearable Sync Lambda

## Overview

**Purpose:** Sync and normalize wearable device data (Apple Watch, Fitbit, Garmin).  
**Runtime:** Python 3.12  
**Trigger:** SQS queue (wearable-sync-queue)

## Features

- Validates wearable data structure
- Normalizes metrics from different device types
- Saves events to DynamoDB
- Calculates daily aggregates (steps, calories, active minutes)
- Supports multiple wearable platforms

## Supported Devices

| Device | Heart Rate | Steps | Calories | Active Minutes |
|--------|------------|-------|----------|----------------|
| Apple Watch | `heartRate` | `steps` | `calories` | `activeMinutes` |
| Fitbit | `heart_rate` | `steps` | `calories_burned` | `active_minutes` |
| Garmin | `hr` | `step_count` | `kcal` | `active_time_minutes` |

## Environment Variables

```bash
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
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

### Apple Watch

```json
{
  "userId": "user-123",
  "deviceType": "apple_watch",
  "deviceId": "watch-001",
  "timestamp": "2024-05-18T14:30:00Z",
  "metrics": {
    "heartRate": 75,
    "steps": 1000,
    "calories": 50,
    "activeMinutes": 10,
    "distance": 0.8
  }
}
```

### Fitbit

```json
{
  "userId": "user-123",
  "deviceType": "fitbit",
  "deviceId": "fitbit-001",
  "timestamp": "2024-05-18T14:30:00Z",
  "metrics": {
    "heart_rate": 75,
    "steps": 1000,
    "calories_burned": 50,
    "active_minutes": 10,
    "distance_meters": 800
  }
}
```

### Garmin

```json
{
  "userId": "user-123",
  "deviceType": "garmin",
  "deviceId": "garmin-001",
  "timestamp": "2024-05-18T14:30:00Z",
  "metrics": {
    "hr": 75,
    "step_count": 1000,
    "kcal": 50,
    "active_time_minutes": 10
  }
}
```

## Normalized Schema

All devices are normalized to:

```json
{
  "heartRate": 75,
  "steps": 1000,
  "calories": 50,
  "activeMinutes": 10,
  "distance": 0.8,
  "sleepMinutes": 480
}
```

## DynamoDB Schema

```json
{
  "userId": "user-123",
  "timestamp": "2024-05-18T14:30:00Z",
  "eventId": "wearable-2024-05-18T14:30:05.123Z",
  "deviceType": "apple_watch",
  "deviceId": "watch-001",
  "metrics": {
    "heartRate": 75,
    "steps": 1000,
    "calories": 50
  },
  "rawMetrics": {...},
  "syncedAt": "2024-05-18T14:30:05Z"
}
```

## Daily Aggregates

Calculates daily totals/averages:

```json
{
  "date": "2024-05-18",
  "totalEvents": 24,
  "totalSteps": 10000,
  "totalCalories": 2000,
  "totalActiveMinutes": 60,
  "averageHeartRate": 72.5
}
```

## Deployment

Lambda configuration:
- **Runtime:** Python 3.12
- **Handler:** handler.lambda_handler
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **IAM:** DynamoDB read/write

## Testing

```bash
pytest tests/ -v
```
