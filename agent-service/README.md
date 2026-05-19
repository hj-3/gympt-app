# Agent Service

## Overview

**Technology:** FastAPI, Python 3.12, AWS Bedrock Claude 3.5 Sonnet  
**Port:** 8001  
**Purpose:** AI agent orchestration using Amazon Bedrock for workout recommendations, posture feedback, and progress analysis.

**Implementation Status:** ✅ Core features implemented (~50% complete)

### Key Features
- Workout plan generation via Claude
- Nutrition advice and meal planning
- Conversational AI personal trainer
- Context-aware recommendations
- Integration with workout history

### Dependencies
- **AWS Bedrock:** Claude 3.5 Sonnet for AI reasoning
- **Redis:** Conversation state and caching
- **DynamoDB:** Agent interaction history
- **SQS:** Async task processing

---

## Development Process Checklist

Follow the [Service Development Process](../docs/service-development-process.md).

### Phase 1: Design & Specification
- [ ] **1. Requirements Definition** - Completed in this README
- [ ] **2. API Specification** - See [docs/api.md](./docs/api.md)
- [ ] **3. Data Model Definition** - DynamoDB schema for interactions
- [ ] **4. Environment Variables** - See [docs/env.md](./docs/env.md)

### Phase 2: Implementation
- [ ] **5. Local Execution Setup** - Instructions below
- [ ] **6. Unit Tests** - See `tests/unit/`
- [ ] **7. Integration Tests** - See `tests/integration/`

### Phase 3: Containerization
- [ ] **8. Dockerfile** - See `Dockerfile`
- [ ] **9. Local Docker Compose Validation** - Test with `../local/docker-compose.yml`

### Phase 4: CI/CD
- [ ] **10. GitHub Actions CI** - See `../.github/workflows/agent-service-ci.yml`
- [ ] **11. Helm Chart Values** - See `../../gympt-gitops/apps/agent-service/`
- [ ] **12. AWS Dev Deployment** - Deploy via Argo CD

### Phase 5: Observability
- [ ] **13. Monitoring Metrics** - Prometheus metrics at `/metrics`
- [ ] **14. Logging and Alerting** - Structured JSON logs

### Phase 6: Production Readiness
- [ ] **15. Production Considerations** - See [docs/deploy.md](./docs/deploy.md)

---

## Quick Start

### Local Development

1. **Create virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export APP_ENV=local
   export MOCK_BEDROCK=true
   export REDIS_HOST=localhost
   # See docs/env.md for full list
   ```

4. **Run application:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

5. **Verify:**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/docs  # OpenAPI docs
   ```

### Docker Compose

```bash
cd ../local
docker compose up -d agent-service
./scripts/local-logs.sh agent-service
```

---

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## API Documentation

- **Local:** http://localhost:8001/docs
- **Dev:** https://agent.dev.gympt.example.com/docs

---

## Project Structure

```
agent-service/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Pydantic settings
│   ├── api/
│   │   └── v1/
│   │       ├── plans.py     # Workout plan endpoints
│   │       ├── chat.py      # Chat endpoints
│   │       └── advice.py    # Nutrition advice endpoints
│   ├── services/
│   │   ├── bedrock.py       # Bedrock client
│   │   ├── agent.py         # Agent orchestration
│   │   └── context.py       # Context management
│   ├── models/
│   │   ├── requests.py      # Request schemas
│   │   └── responses.py     # Response schemas
│   └── utils/
│       ├── logger.py        # Structured logging
│       └── metrics.py       # Prometheus metrics
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── api.md
│   ├── env.md
│   ├── test.md
│   └── deploy.md
├── requirements.txt
├── Dockerfile
└── README.md
```

---

**Last Updated:** 2026-05-18  
**Maintainer:** AI/ML Team
