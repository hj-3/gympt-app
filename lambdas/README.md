# GymPT Lambda Functions

## Overview

This directory contains 8 AWS Lambda functions for the GymPT platform. All Lambdas are implemented in Python 3.12 with structured logging, environment-based configuration, and comprehensive test coverage.

## Common Features

- **Runtime:** Python 3.12
- **Structured Logging:** JSON logs via python-json-logger
- **Environment Variables:** Pydantic-style configuration
- **Error Handling:** Graceful failures with detailed logging
- **Testing:** pytest with mocks for AWS services
- **Local Testing:** Event examples for quick validation

## Lambda Functions

### 1. agent-action

**Purpose:** Bedrock Agent Action Group handler  
**Trigger:** Bedrock Agent invocation  
**Functions:**
- getUserProfile
- getBodyProfile
- getRecentWorkoutSessions
- saveWorkoutRecommendation
- getPostureAnalysisResult
- createWorkoutReport

**Key Dependencies:** DynamoDB, SQS

### 2. report-generator

**Purpose:** Generate workout performance reports with AI insights  
**Trigger:** SQS (report-generation-queue)  
**Features:**
- Bedrock integration with mock support
- Aggregates workout sessions and posture events
- Saves reports to S3
- Publishes notifications

**Key Dependencies:** DynamoDB, S3, Bedrock, SQS

### 3. posture-event-processor

**Purpose:** Process and enrich real-time posture analysis events  
**Trigger:** SQS (posture-event-queue)  
**Features:**
- Enriches events with calculated metrics
- Aggregates issues by type/severity
- Publishes CloudWatch custom metrics
- Saves to DynamoDB

**Key Dependencies:** DynamoDB, CloudWatch

### 4. thumbnail-generator

**Purpose:** Generate video thumbnails from workout recordings  
**Trigger:** S3 ObjectCreated or SQS  
**Features:**
- Mock thumbnail generation (Pillow)
- Production-ready structure for ffmpeg/opencv
- S3 storage with caching headers

**Key Dependencies:** S3, Pillow

### 5. wearable-sync

**Purpose:** Sync and normalize wearable device data  
**Trigger:** SQS (wearable-sync-queue)  
**Supported Devices:**
- Apple Watch
- Fitbit
- Garmin

**Features:**
- Normalizes metrics across platforms
- Calculates daily aggregates
- Stores events in DynamoDB

**Key Dependencies:** DynamoDB

### 6. recommendation-update

**Purpose:** Adjust workout intensity based on performance  
**Trigger:** EventBridge rule or SQS  
**Logic:**
- Analyzes last 5 sessions
- INCREASE: Avg score ≥8.5 AND completion ≥90%
- DECREASE: Avg score <6.0 OR completion <50%
- MAINTAIN: Otherwise

**Features:**
- Updates Backend API via REST
- Saves recommendation history

**Key Dependencies:** DynamoDB, Backend API

### 7. notification

**Purpose:** Multi-channel notification dispatcher  
**Trigger:** SQS (notification-queue)  
**Channels:**
- Slack (webhook)
- Email (SNS)
- Push (SNS Mobile - mock)

**Notification Types:**
- REPORT_READY
- RECOMMENDATION_UPDATE
- WORKOUT_COMPLETED
- POSTURE_ALERT
- GOAL_ACHIEVED

**Key Dependencies:** SNS, Slack API

### 8. export

**Purpose:** Export user workout data with pre-signed URLs  
**Trigger:** Direct invocation, API Gateway, or SQS  
**Formats:**
- CSV
- JSON

**Features:**
- Exports workout sessions + body profiles
- Configurable date range (default: 30 days)
- Pre-signed URLs (1 hour expiry)
- S3 lifecycle policy ready

**Key Dependencies:** DynamoDB, S3

## Architecture

```
EventBridge                    S3 Events
     │                              │
     ├─► recommendation-update      ├─► thumbnail-generator
     │                              │
     │                              │
SQS Queues                          │
     │                              │
     ├─► report-generator ──────────┤
     ├─► posture-event-processor    │
     ├─► wearable-sync              │
     ├─► notification               │
     └─► export (optional)          │
                                    │
Bedrock Agent                       │
     │                              │
     └─► agent-action               │
                                    │
API Gateway                         │
     │                              │
     └─► export ────────────────────┘
```

## Deployment

### Common Environment Variables

```bash
# AWS
AWS_REGION=ap-northeast-2
DYNAMODB_TABLE_PREFIX=gympt-dev
S3_BUCKET=gympt-videos

# Backend API
BACKEND_API_URL=https://api.dev.gympt.com
BACKEND_API_KEY=secret

# Feature Flags
ENABLE_BEDROCK_MOCK=true
ENABLE_SLACK=false
ENABLE_EMAIL=false
```

### IAM Permissions

Each Lambda requires specific IAM permissions:

**agent-action:**
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:Query",
    "dynamodb:PutItem",
    "sqs:SendMessage"
  ],
  "Resource": ["*"]
}
```

**report-generator:**
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:Query",
    "s3:PutObject",
    "sqs:SendMessage",
    "bedrock:InvokeModel"
  ],
  "Resource": ["*"]
}
```

### Terraform Example

```hcl
resource "aws_lambda_function" "agent_action" {
  filename         = "agent-action.zip"
  function_name    = "gympt-agent-action"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.12"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      DYNAMODB_TABLE_PREFIX = "gympt-${var.environment}"
      AWS_REGION           = var.aws_region
    }
  }
}
```

## Local Development

### Setup

```bash
# Navigate to any Lambda directory
cd agent-action

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

### Test with Example Event

```bash
python -c "
import json
from handler import lambda_handler

with open('event.example.json') as f:
    event = json.load(f)

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

### LocalStack Testing

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Set endpoint override
export AWS_ENDPOINT_URL=http://localhost:4566

# Create tables and queues
aws dynamodb create-table --endpoint-url $AWS_ENDPOINT_URL \
  --table-name gympt-local-workout-sessions \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Testing

All Lambdas include comprehensive pytest test suites:

```bash
# Run all tests
find . -name "tests" -type d -exec pytest {}/../tests/ -v \;

# Run with coverage
pytest --cov=handler --cov-report=html tests/

# Run specific test
pytest tests/test_handler.py::test_lambda_handler_success -v
```

## Monitoring

### CloudWatch Metrics

- **agent-action:** Invocations, Errors, Duration
- **posture-event-processor:** Custom metrics (PostureScore, IssueCount)
- **All:** Lambda standard metrics

### Alarms

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name gympt-lambda-errors \
  --alarm-description "Lambda error rate > 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

## CI/CD

GitHub Actions workflow example:

```yaml
name: Lambda CI

on:
  push:
    paths:
      - 'lambdas/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd lambdas/${{ matrix.lambda }}
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd lambdas/${{ matrix.lambda }}
          pytest tests/ -v
    
    strategy:
      matrix:
        lambda:
          - agent-action
          - report-generator
          - posture-event-processor
          - thumbnail-generator
          - wearable-sync
          - recommendation-update
          - notification
          - export
```

## Performance Considerations

| Lambda | Memory | Timeout | Concurrency |
|--------|--------|---------|-------------|
| agent-action | 512 MB | 30s | 100 |
| report-generator | 512 MB | 60s | 10 |
| posture-event-processor | 256 MB | 30s | 100 |
| thumbnail-generator | 1024 MB | 60s | 50 |
| wearable-sync | 256 MB | 30s | 100 |
| recommendation-update | 256 MB | 30s | 50 |
| notification | 256 MB | 30s | 100 |
| export | 512 MB | 60s | 20 |

## Cost Optimization

1. **Use Reserved Concurrency** for predictable workloads
2. **Enable S3 Event Filtering** to reduce unnecessary invocations
3. **Batch SQS Messages** (up to 10 messages per invocation)
4. **Use Provisioned Concurrency** only for latency-sensitive functions
5. **Set Appropriate Memory** - Lambda charges by GB-second

## Security

- **Secrets:** Use AWS Secrets Manager or SSM Parameter Store
- **IAM:** Follow least privilege principle
- **VPC:** Optional for RDS access (adds cold start latency)
- **Encryption:** Enable at-rest encryption for S3/DynamoDB
- **API Keys:** Rotate Backend API keys regularly

## Troubleshooting

### Common Issues

**Lambda timeout:**
- Increase timeout in configuration
- Optimize DynamoDB queries (use indexes)
- Batch operations where possible

**Memory errors:**
- Increase memory allocation
- Stream large S3 objects instead of loading into memory

**DynamoDB throttling:**
- Use exponential backoff
- Increase table provisioned capacity
- Switch to on-demand billing mode

**Cold starts:**
- Use Provisioned Concurrency for critical paths
- Minimize package size
- Use Lambda layers for shared dependencies

## Next Steps

1. **Implement remaining business logic** in agent-action
2. **Add real video processing** to thumbnail-generator (ffmpeg layer)
3. **Integrate real push notifications** in notification Lambda
4. **Add retry logic** with SQS Dead Letter Queues
5. **Implement API Gateway** for export Lambda
6. **Add X-Ray tracing** for distributed debugging

## Maintainer

AI/ML Team  
Last Updated: 2024-05-19
