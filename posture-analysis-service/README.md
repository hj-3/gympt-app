# Posture Analysis Service

## Overview

**Technology:** FastAPI, Python 3.11, MediaPipe, OpenCV  
**Port:** 8002  
**Purpose:** Real-time posture analysis and form correction using ML models (MediaPipe Pose, custom LSTM).

### Key Features
- Real-time pose estimation from video frames
- Exercise form analysis and scoring
- Posture anomaly detection
- Integration with Kinesis Video Streams
- Event publishing to SQS/DynamoDB

### Dependencies
- **ML Framework:** MediaPipe, TensorFlow/PyTorch
- **Video Input:** Kinesis Video Streams
- **Storage:** S3 (video clips), DynamoDB (events)
- **Queue:** SQS (posture events)
- **Redis:** Frame caching

---

## Development Process Checklist

### Phase 1: Design & Specification
- [ ] **1. Requirements Definition** - Completed
- [ ] **2. API Specification** - See [docs/api.md](./docs/api.md)
- [ ] **3. Data Model Definition** - Pose landmarks schema
- [ ] **4. Environment Variables** - See [docs/env.md](./docs/env.md)

### Phase 2: Implementation
- [ ] **5. Local Execution Setup** - Instructions below
- [ ] **6. Unit Tests** - See `tests/unit/`
- [ ] **7. Integration Tests** - See `tests/integration/`

### Phase 3-6: Containerization, CI/CD, Observability, Production
- [ ] **8-15.** Follow standard process

---

## Quick Start

### Local Development

```bash
# Install dependencies (CPU version)
pip install -r requirements.txt

# For GPU support (optional)
pip install -r requirements-gpu.txt

# Run
export APP_ENV=local
export MODEL_TYPE=mediapipe
export ENABLE_GPU=false
uvicorn app.main:app --reload --port 8002
```

### Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires video samples)
pytest tests/integration/ -v --video-samples=tests/fixtures/videos/
```

---

## ML Models

### MediaPipe Pose
- **Purpose:** Real-time pose landmark detection
- **Accuracy:** 95%+ on standard exercises
- **Latency:** < 50ms per frame

### Custom LSTM Model
- **Purpose:** Temporal analysis for rep counting
- **Training Data:** 10,000+ labeled workout videos
- **Accuracy:** 92%

**Model Files:** `models/lstm_rep_counter.h5`

---

## API Endpoints

- `POST /api/v1/analyze/frame` - Analyze single frame
- `POST /api/v1/sessions/{id}/start` - Start analysis session
- `POST /api/v1/sessions/{id}/stop` - Stop session
- `GET /api/v1/sessions/{id}/results` - Get analysis results

---

**Last Updated:** 2026-05-18  
**Maintainer:** ML Team
