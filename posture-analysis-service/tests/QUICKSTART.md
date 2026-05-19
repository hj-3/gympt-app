# Quick Start - Running Tests

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (required for integration tests)
docker run -d -p 6379:6379 redis:7-alpine

# Start LocalStack (optional, for AWS integration tests)
docker run -d -p 4566:4566 localstack/localstack
```

## Run Tests

### 1. Quick Tests (Development)
Fastest option for rapid feedback during development:
```bash
./tests/run_quick_tests.sh
```

### 2. All Tests
Complete test suite:
```bash
./tests/run_all_tests.sh
```

### 3. Specific Category
```bash
# Unit tests only
pytest tests/unit/ -v

# WebSocket tests
pytest tests/websocket/ -v

# E2E tests
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v
```

### 4. With Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### 5. Docker (Complete Environment)
```bash
docker-compose -f docker-compose.test.yml up
```

## Test Markers

Run specific test types using markers:

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

# Skip slow tests
pytest -m "not slow"

# Skip GPU tests
pytest -m "not gpu"
```

## Common Commands

```bash
# Run single test file
pytest tests/unit/test_rep_counter.py -v

# Run single test
pytest tests/unit/test_rep_counter.py::TestRepCounter::test_squat_rep_counting -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Verbose output
pytest -vv

# Show test durations
pytest --durations=10

# Run failed tests only
pytest --lf
```

## Troubleshooting

### Redis Connection Failed
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis if not running
docker run -d -p 6379:6379 redis:7-alpine
```

### Import Errors
```bash
# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Timeout Errors
```bash
# Increase timeout
pytest --timeout=60
```

### Too Many Open Files
```bash
# Increase file descriptor limit (macOS/Linux)
ulimit -n 4096
```

## Test Reports

After running tests, reports are available in:
- **Coverage:** `htmlcov/index.html`
- **Test Results:** `test-reports/`
- **JUnit XML:** `test-reports/junit-*.xml`

## Next Steps

1. Read [tests/README.md](README.md) for detailed information
2. Check [tests/TESTING_GUIDE.md](TESTING_GUIDE.md) for best practices
3. Review [TESTING_IMPLEMENTATION_SUMMARY.md](../TESTING_IMPLEMENTATION_SUMMARY.md) for overview

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests
- GitHub Actions workflow: `.github/workflows/tests.yml`

View results at: `https://github.com/your-org/gympt-app/actions`
