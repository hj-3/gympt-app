# KVS Consumer Service

AWS Kinesis Video Streams Consumer service for GYMPT platform.

## Overview

This service consumes video streams from AWS KVS WebRTC channels and forwards frames to the Posture Analysis Service for real-time form analysis.

## Features

- **KVS WebRTC Consumer**: Consumes video streams from AWS Kinesis Video Streams
- **Frame Sampling**: Processes frames at configurable sample rate
- **Real-time Processing**: Forwards frames to Posture Analysis Service
- **Session Management**: Manages multiple concurrent stream consumers
- **Health Monitoring**: CloudWatch metrics and health checks

## Architecture

```
Frontend (KVS WebRTC MASTER)
    ↓
AWS KVS Signaling Channel
    ↓
KVS Consumer Service (VIEWER)
    ↓
Posture Analysis Service
    ↓
WebSocket → Frontend
```

## API Endpoints

### Start Consumer
```bash
POST /api/v1/consume/start
{
  "channel_name": "prod-gympt-workout-signaling",
  "session_id": "session-123",
  "user_id": "user-456",
  "exercise": "squat"
}
```

### Stop Consumer
```bash
POST /api/v1/consume/stop
{
  "session_id": "session-123"
}
```

### Consumer Status
```bash
GET /api/v1/consume/status/{session_id}
```

### List Active Consumers
```bash
GET /api/v1/consume/active
```

## Configuration

Environment variables:

- `AWS_REGION`: AWS region (default: ap-northeast-2)
- `KVS_CHANNEL_PREFIX`: KVS channel name prefix
- `POSTURE_ANALYSIS_URL`: Posture Analysis Service URL
- `FRAME_SAMPLE_RATE`: Process every Nth frame (default: 10)
- `LOG_LEVEL`: Logging level (default: INFO)

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn src.main:app --reload --port 8003
```

### Docker Build

```bash
docker build -t kvs-consumer-service .
docker run -p 8003:8003 kvs-consumer-service
```

## Deployment

Deployed via Argo CD GitOps:

1. Docker image pushed to ECR
2. GitOps repo updated with new image tag
3. Argo CD syncs to EKS cluster

## IAM Permissions Required

- `kinesisvideo:DescribeSignalingChannel`
- `kinesisvideo:GetSignalingChannelEndpoint`
- `kinesisvideo:GetIceServerConfig`
- `kinesisvideo:ConnectAsViewer`
- `kinesisvideo:GetDataEndpoint`
- `kinesisvideo:GetMedia`

## Monitoring

Metrics exported to Prometheus:
- Frame processing rate
- Consumer count
- Error rate
- Latency

## Notes

- KVS WebRTC is used for low-latency video streaming
- Frames are sampled to reduce processing load
- Consumer automatically stops when session ends
- Supports multiple concurrent sessions
