# GYMPT Agent Service - Test Suite

Comprehensive test suite for the GYMPT Agent Service with 80%+ coverage target.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── docker-compose.test.yml  # Test infrastructure (Redis, DynamoDB, LocalStack)
│
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_bedrock_client.py
│   ├── test_redis_cache.py
│   └── services/
│       ├── test_agent_service.py
│       └── test_cache_service.py
│
├── integration/             # Integration tests (requires Docker services)
│   ├── test_agent_service.py
│   ├── test_backend_integration.py
│   ├── test_cache_integration.py
│   ├── test_dynamodb_logging.py
│   ├── test_prompt_rendering.py
│   └── test_sqs_publishing.py
│
├── e2e/                     # End-to-end tests (full flow)
│   ├── test_workout_recommendation_e2e.py
│   ├── test_posture_feedback_e2e.py
│   └── test_report_generation_e2e.py
│
├── api/                     # API endpoint tests
│   ├── test_health_endpoint.py
│   ├── test_workout_api.py
│   └── test_error_handling.py
│
├── performance/             # Performance and load tests
│   └── test_load_bedrock.py
│
├── regression/              # Regression tests
│   └── test_api_contract.py
│
└── utils/                   # Test utilities
    ├── assertions.py        # Custom assertions
    └── helpers.py           # Test data generators
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m e2e            # End-to-end tests
pytest -m smoke          # Smoke tests (critical paths)
```

### Test Markers

Tests are organized with pytest markers:

- `unit`: Fast unit tests, no external dependencies
- `integration`: Integration tests, requires Docker services
- `e2e`: End-to-end tests, full application flow
- `performance`: Performance and load tests
- `regression`: Regression tests for API stability
- `smoke`: Critical path tests for CI/CD
- `slow`: Long-running tests
- `requires_bedrock`: Tests requiring real Bedrock (skip in CI)
- `requires_aws`: Tests requiring AWS services

### Running by Category

```bash
# Unit tests (fastest)
pytest -m unit -v

# Integration tests (requires Docker)
pytest -m integration -v

# E2E tests
pytest -m e2e -v

# Smoke tests (CI-friendly)
pytest -m smoke -v

# Performance tests (slow)
pytest -m performance -v

# All except slow tests
pytest -m "not slow" -v
```

### Test Infrastructure

#### Start Test Services

```bash
# Start Redis, DynamoDB, and LocalStack
cd tests
docker-compose -f docker-compose.test.yml up -d

# Check service health
docker-compose -f docker-compose.test.yml ps

# View logs
docker-compose -f docker-compose.test.yml logs -f

# Stop services
docker-compose -f docker-compose.test.yml down
```

#### Service URLs

- **Redis**: `localhost:6379`
- **DynamoDB Local**: `http://localhost:8000`
- **LocalStack**: `http://localhost:4566`

## Test Configuration

### Environment Variables

Create a `.env.test` file:

```bash
APP_ENV=test
ENABLE_BEDROCK_MOCK=true
REDIS_HOST=localhost
REDIS_PORT=6379
DYNAMODB_ENDPOINT_URL=http://localhost:8000
SQS_ENDPOINT_URL=http://localhost:4566
BACKEND_API_BASE_URL=http://mock-backend
```

### pytest.ini

Test configuration is in `pytest.ini`:

```ini
[pytest]
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    smoke: Smoke tests
```

## Coverage Requirements

- **Overall**: 80%+
- **Service Layer**: 90%+
- **Routers**: 85%+
- **Clients**: 80%+

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=app --cov-report=xml
```

## Parallel Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Auto-detect CPU count
pytest -n auto
```

## Writing New Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.unit
@pytest.mark.asyncio
async def test_my_service(mock_bedrock_client):
    """Test my service method."""
    # Arrange
    mock_bedrock_client.invoke_model.return_value = {"content": "test"}
    
    # Act
    result = await my_service.do_something()
    
    # Assert
    assert result is not None
    mock_bedrock_client.invoke_model.assert_called_once()
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_integration(redis_connection):
    """Test Redis integration."""
    await redis_connection.set("test:key", "value")
    result = await redis_connection.get("test:key")
    
    assert result == "value"
```

### E2E Test Example

```python
import pytest
from fastapi import status

@pytest.mark.e2e
@pytest.mark.smoke
def test_workout_recommendation_flow(test_client, sample_workout_request):
    """Test complete workout recommendation flow."""
    response = test_client.post(
        "/agent/workout/recommend",
        json=sample_workout_request
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "recommendation" in data
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
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run smoke tests
        run: pytest -m smoke -v
      
      - name: Run unit tests
        run: pytest -m unit --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

```bash
# Run with verbose output
pytest -vv

# Run single test
pytest tests/unit/test_bedrock_client.py::test_mock_response_workout -v

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Run last failed tests
pytest --lf

# Run tests matching pattern
pytest -k "workout" -v
```

## Performance Testing

```bash
# Run performance tests
pytest -m performance -v

# With benchmark report
pytest -m benchmark --benchmark-only

# Generate performance report
pytest -m performance --benchmark-save=baseline
```

## Best Practices

1. **Use Fixtures**: Leverage fixtures from `conftest.py`
2. **Mock External Services**: Use mocks for Bedrock, Backend API, AWS
3. **Test Isolation**: Each test should be independent
4. **Clear Assertions**: Use descriptive assertion messages
5. **Test Both Paths**: Test success and error cases
6. **Performance Aware**: Keep unit tests fast (< 100ms)
7. **Coverage Goals**: Aim for 80%+ overall coverage

## Common Issues

### Redis Connection Failed

```bash
# Start Redis
docker-compose -f tests/docker-compose.test.yml up redis -d

# Or skip integration tests
pytest -m "not integration"
```

### Import Errors

```bash
# Ensure app is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Slow Tests

```bash
# Skip slow tests
pytest -m "not slow"

# Run only fast unit tests
pytest -m unit
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## Support

For questions or issues with tests, contact the development team or open an issue in the repository.
