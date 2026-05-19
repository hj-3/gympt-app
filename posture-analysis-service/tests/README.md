# GYMPT Posture Analysis Service - Test Suite

Comprehensive test suite for the GYMPT Posture Analysis Service covering WebSocket communication, pose estimation, rep counting, exercise rules, and performance testing.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── utils/                         # Test utilities
│   ├── landmark_generator.py     # Generate realistic pose landmarks
│   ├── websocket_client.py       # WebSocket test helpers
│   └── assertions.py             # Custom assertions
├── websocket/                     # WebSocket tests
│   ├── test_websocket_connection.py
│   └── test_websocket_messaging.py
├── e2e/                          # End-to-end tests
│   ├── test_squat_analysis_e2e.py
│   ├── test_pushup_analysis_e2e.py
│   └── test_session_lifecycle_e2e.py
├── unit/                         # Unit tests
│   ├── pose_estimator/
│   ├── counting/
│   ├── rules/
│   ├── services/
│   └── streaming/
├── integration/                   # Integration tests
│   ├── test_dynamodb_integration.py
│   ├── test_s3_integration.py
│   └── test_redis_pubsub_integration.py
├── performance/                   # Performance tests
│   ├── test_websocket_performance.py
│   └── test_mediapipe_performance.py
├── gpu/                          # GPU tests
│   └── test_gpu_availability.py
└── regression/                    # Regression tests
    └── test_rep_count_regression.py
```

## Quick Start

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# WebSocket tests
pytest -m websocket

# Performance tests
pytest -m performance

# GPU tests (requires CUDA)
pytest -m gpu

# Exclude slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

View coverage report:
```bash
open htmlcov/index.html
```

## Test Environment Setup

### Local Testing

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

3. **Start LocalStack (for AWS services):**
```bash
docker run -d -p 4566:4566 localstack/localstack
```

4. **Set environment variables:**
```bash
export APP_ENV=test
export MODEL_TYPE=mock
export REDIS_HOST=localhost
export DYNAMODB_ENDPOINT_URL=http://localhost:4566
export S3_ENDPOINT_URL=http://localhost:4566
export SQS_ENDPOINT_URL=http://localhost:4566
```

5. **Run tests:**
```bash
pytest
```

### Docker Testing

Use docker-compose for complete test environment:

```bash
# Run all tests in containers
docker-compose -f docker-compose.test.yml up

# Run specific service
docker-compose -f docker-compose.test.yml up test-runner

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation:
- Pose estimator
- Rep counter
- Exercise rules
- Feedback service
- Services and clients

**Run:**
```bash
pytest tests/unit/ -v
```

### Integration Tests (`tests/integration/`)

Test component interactions:
- DynamoDB integration
- S3 integration
- Redis pub/sub
- MediaPipe estimator

**Run:**
```bash
pytest tests/integration/ -v
```

### E2E Tests (`tests/e2e/`)

Test complete workflows:
- Full squat session
- Pushup session
- Session lifecycle
- Form analysis

**Run:**
```bash
pytest tests/e2e/ -v
```

### WebSocket Tests (`tests/websocket/`)

Test WebSocket functionality:
- Connection management
- Message handling
- Frame processing
- Concurrent connections

**Run:**
```bash
pytest tests/websocket/ -v
```

### Performance Tests (`tests/performance/`)

Test performance characteristics:
- Throughput (FPS)
- Latency (P50, P95, P99)
- Concurrent connections
- Memory usage

**Run:**
```bash
pytest tests/performance/ -v
```

**Note:** Performance tests may take longer to run.

### GPU Tests (`tests/gpu/`)

Test GPU acceleration:
- GPU availability
- GPU vs CPU performance
- Memory management

**Requirements:**
- CUDA-capable GPU
- PyTorch with CUDA support

**Run:**
```bash
pytest tests/gpu/ -v
```

**Skip if no GPU:**
Tests automatically skip if GPU is not available.

## Test Fixtures

### Common Fixtures (in `conftest.py`)

- `test_client` - FastAPI TestClient
- `mock_pose_data` - Generic pose data
- `mock_squat_down_pose` - Squat down position
- `mock_squat_up_pose` - Squat up position
- `sample_frame_480p` - 480p test frame
- `base64_encoded_frame` - Base64-encoded frame
- `mock_dynamodb` - Mocked DynamoDB
- `mock_s3` - Mocked S3
- `mock_sqs` - Mocked SQS
- `mock_redis` - Mocked Redis
- `squat_rep_sequence` - 10 squat rep sequence
- `pushup_rep_sequence` - 20 pushup rep sequence

### Using Fixtures

```python
async def test_example(test_client, base64_encoded_frame):
    with test_client.websocket_connect("/ws/posture/test") as ws:
        ws.send_json({"type": "frame", "frame": base64_encoded_frame})
```

## Test Utilities

### Landmark Generator

Generate realistic pose landmarks for testing:

```python
from tests.utils.landmark_generator import LandmarkGenerator

gen = LandmarkGenerator()

# Generate squat landmarks
keypoints = gen.generate_squat_landmarks(depth=0.8, knee_valgus=0.0)

# Generate rep sequence
sequence = gen.generate_rep_sequence("squat", num_reps=10)
```

### Custom Assertions

Use custom assertions for better error messages:

```python
from tests.utils.assertions import (
    assert_rep_count,
    assert_score_in_range,
    assert_landmarks_valid
)

# Assert rep count
assert_rep_count(result, expected_reps=10, tolerance=1)

# Assert score range
assert_score_in_range(analysis, min_score=7.0, max_score=10.0)

# Assert landmarks are valid
assert_landmarks_valid(pose_data, required_keypoints=["left_hip", "right_hip"])
```

## Coverage Requirements

Target coverage by component:

- **Overall:** 80%+
- **WebSocket handler:** 90%+
- **Pose estimator:** 85%+
- **Rep counter:** 95%+
- **Exercise rules:** 95%+
- **Services:** 90%+

Check current coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
      localstack:
        image: localstack/localstack

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

### Run Single Test

```bash
pytest tests/unit/test_rep_counter.py::TestRepCounter::test_squat_rep_counting -v
```

### Print Debug Output

```bash
pytest tests/ -v -s
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Increase Verbosity

```bash
pytest tests/ -vv
```

## Performance Testing

### Benchmark Performance

```bash
# Run performance tests with timing
pytest tests/performance/ -v --durations=10
```

### Profile Tests

```bash
# Install pytest-profiling
pip install pytest-profiling

# Run with profiling
pytest tests/performance/ --profile
```

## Known Issues

1. **WebSocket Tests in Docker:** Some WebSocket tests may be flaky in Docker due to timing. Use `--retry` flag if needed.

2. **GPU Tests:** GPU tests require CUDA. They will skip automatically if GPU is not available.

3. **Performance Tests:** Results may vary based on system resources. Use relative comparisons rather than absolute thresholds.

## Contributing

When adding new tests:

1. Place in appropriate directory
2. Use descriptive test names
3. Add docstrings
4. Use appropriate markers (`@pytest.mark.unit`, etc.)
5. Add fixtures to `conftest.py` if reusable
6. Update this README

## Troubleshooting

### Tests Timeout

Increase timeout in `pytest.ini`:
```ini
timeout = 60
```

### Redis Connection Failed

Ensure Redis is running:
```bash
docker ps | grep redis
```

Start if not running:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Import Errors

Ensure app is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Coverage Not Working

Install coverage dependencies:
```bash
pip install pytest-cov coverage
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
