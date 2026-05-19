# GYMPT Agent Service - Testing Guide

Comprehensive guide for writing and maintaining tests for the GYMPT Agent Service.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Categories](#test-categories)
3. [Writing Tests](#writing-tests)
4. [Best Practices](#best-practices)
5. [Mocking Strategy](#mocking-strategy)
6. [Performance Testing](#performance-testing)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

## Testing Philosophy

### Test Pyramid

```
        /\
       /  \      E2E Tests (10%)
      /----\     - Full application flow
     /      \    - Realistic scenarios
    /--------\   
   /          \  Integration Tests (30%)
  /------------\ - Component interaction
 /              \- External services
/----------------\
|                | Unit Tests (60%)
|________________| - Fast, isolated
                   - Single responsibility
```

### Coverage Goals

- **Overall**: 80%+
- **Critical Paths**: 95%+
- **Service Layer**: 90%+
- **API Endpoints**: 85%+
- **Utilities**: 80%+

## Test Categories

### Unit Tests

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast (< 100ms per test)
- No external dependencies
- Heavily mocked
- Focus on single responsibility

**When to use**:
- Testing business logic
- Testing utility functions
- Testing data transformations
- Testing error handling

**Example**:
```python
@pytest.mark.unit
def test_cache_key_generation():
    """Test cache key is deterministic."""
    from app.services.cache_service import CacheService
    
    service = CacheService()
    
    key1 = service.generate_cache_key("endpoint", "user", {"a": 1})
    key2 = service.generate_cache_key("endpoint", "user", {"a": 1})
    
    assert key1 == key2
```

### Integration Tests

**Purpose**: Test component interactions with real services

**Characteristics**:
- Moderate speed (100ms - 1s)
- Uses real services (Redis, DynamoDB)
- Tests actual integration
- May use Docker containers

**When to use**:
- Testing database operations
- Testing cache behavior
- Testing API client interactions
- Testing template rendering

**Example**:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_integration(redis_connection):
    """Test Redis cache with real instance."""
    key = "test:key"
    value = {"data": "test"}
    
    await redis_connection.set(key, json.dumps(value), ex=60)
    cached = await redis_connection.get(key)
    
    assert json.loads(cached) == value
```

### E2E Tests

**Purpose**: Test complete user flows

**Characteristics**:
- Slower (1s - 5s)
- Tests entire request/response cycle
- Validates integration of all components
- Closest to production behavior

**When to use**:
- Testing critical user journeys
- Testing API contracts
- Smoke testing
- Regression testing

**Example**:
```python
@pytest.mark.e2e
@pytest.mark.smoke
def test_workout_recommendation_flow(test_client, all_mocks):
    """Test complete workout recommendation flow."""
    response = test_client.post(
        "/agent/workout/recommend",
        json=sample_request
    )
    
    assert response.status_code == 200
    assert "recommendation" in response.json()
```

### Performance Tests

**Purpose**: Verify performance characteristics

**Characteristics**:
- Long-running (5s - 60s)
- Tests load and concurrency
- Measures response times
- Checks for memory leaks

**When to use**:
- Testing concurrent requests
- Measuring response time distribution
- Load testing
- Regression testing for performance

**Example**:
```python
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test 50 concurrent requests."""
    tasks = [make_request() for _ in range(50)]
    results = await asyncio.gather(*tasks)
    
    assert all(r is not None for r in results)
```

## Writing Tests

### Test Structure (AAA Pattern)

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_something():
    """Test description."""
    # Arrange - Set up test data and mocks
    mock_client = Mock()
    mock_client.method.return_value = "result"
    
    # Act - Execute the code under test
    result = await service.do_something()
    
    # Assert - Verify expectations
    assert result == "expected"
    mock_client.method.assert_called_once()
```

### Test Naming

Use descriptive test names that explain:
1. What is being tested
2. What conditions/inputs
3. What is expected

```python
# Good
def test_generate_workout_plan_with_injury_limitations()
def test_cache_key_generation_is_deterministic()
def test_posture_feedback_severity_detection_high()

# Bad
def test_workout()
def test_cache()
def test_posture()
```

### Test Documentation

```python
@pytest.mark.unit
def test_cache_key_collision_resistance():
    """
    Test cache key generation avoids collisions.
    
    Generates 100 keys with different inputs and verifies
    all keys are unique. This ensures the hashing algorithm
    provides sufficient collision resistance.
    """
    # Test implementation
```

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
# Good - Uses fresh fixtures
def test_something(mock_client):
    mock_client.method.return_value = "test"
    # Test code

# Bad - Relies on shared state
global_state = {}

def test_something():
    global_state["key"] = "value"  # Affects other tests
```

### 2. Use Fixtures

Leverage pytest fixtures for setup:

```python
@pytest.fixture
def sample_request():
    """Reusable sample request."""
    return {
        "user_id": "test-user",
        "goal": "muscle_gain"
    }

def test_something(sample_request):
    # Use sample_request
    pass
```

### 3. Test Both Success and Failure

```python
# Success case
@pytest.mark.unit
async def test_api_call_success(mock_client):
    mock_client.call.return_value = {"success": True}
    result = await service.make_call()
    assert result["success"] is True

# Failure case
@pytest.mark.unit
async def test_api_call_failure(mock_client):
    mock_client.call.side_effect = Exception("API error")
    
    with pytest.raises(Exception):
        await service.make_call()
```

### 4. Clear Assertions

```python
# Good - Clear and specific
assert response.status_code == 200
assert "recommendation" in data
assert len(data["key_insights"]) > 0

# Bad - Vague
assert response
assert data
```

### 5. Avoid Test Logic

```python
# Good - Simple and direct
def test_something():
    result = function_to_test(5)
    assert result == 25

# Bad - Has logic
def test_something():
    for i in range(10):
        if i % 2 == 0:
            result = function_to_test(i)
            # Complex assertions
```

## Mocking Strategy

### When to Mock

**Mock**:
- External API calls (Backend API, Bedrock)
- Database operations (in unit tests)
- Time-dependent functions
- Random number generation
- File I/O

**Don't Mock**:
- The code under test
- Simple data structures
- Standard library functions (unless time/random)
- Integration test dependencies

### Mock Examples

#### Mock Async Function

```python
from unittest.mock import AsyncMock

mock_client = Mock()
mock_client.invoke_model = AsyncMock(return_value={
    "content": "test",
    "model": "test-model"
})
```

#### Mock with Side Effects

```python
# Different return values for multiple calls
mock_client.method.side_effect = ["first", "second", "third"]

# Raise exception
mock_client.method.side_effect = Exception("Error")
```

#### Patch Context Manager

```python
with patch("app.services.agent_service.bedrock_client", mock_client):
    result = await service.do_something()
```

## Performance Testing

### Guidelines

1. **Mark as slow**: `@pytest.mark.slow`
2. **Set realistic expectations**: Based on production requirements
3. **Measure percentiles**: P50, P95, P99
4. **Test concurrency**: Simulate realistic load
5. **Check for leaks**: Monitor memory usage

### Example

```python
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_response_time_distribution():
    """Test response time meets SLA."""
    response_times = []
    
    for _ in range(100):
        start = time.time()
        await make_request()
        response_times.append(time.time() - start)
    
    response_times.sort()
    p95 = response_times[94]
    
    # SLA: 95th percentile < 1 second
    assert p95 < 1.0
```

## Common Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Testing Exceptions

```python
def test_raises_exception():
    with pytest.raises(ValueError) as exc_info:
        raise_error()
    
    assert "expected message" in str(exc_info.value)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("beginner", "low"),
    ("intermediate", "medium"),
    ("advanced", "high"),
])
def test_difficulty_mapping(input, expected):
    result = map_difficulty(input)
    assert result == expected
```

### Testing Time-Dependent Code

```python
from freezegun import freeze_time

@freeze_time("2024-01-01 12:00:00")
def test_time_dependent():
    result = get_current_time()
    assert result.year == 2024
```

## Troubleshooting

### Test Fails Intermittently

**Causes**:
- Race conditions
- Shared state
- Time-dependent code
- Random values

**Solutions**:
- Use fixtures for isolation
- Mock time and random
- Add proper test cleanup
- Use deterministic data

### Tests Too Slow

**Causes**:
- Too many integration tests
- Not using mocks
- Inefficient test setup

**Solutions**:
- Convert to unit tests where possible
- Use mocks for external services
- Optimize fixtures
- Run tests in parallel

### Coverage Not Improving

**Causes**:
- Missing edge cases
- Error paths not tested
- Complex conditionals

**Solutions**:
- Check coverage report: `pytest --cov=app --cov-report=html`
- Add tests for uncovered lines
- Test error conditions
- Simplify complex logic

### Import Errors

**Causes**:
- PYTHONPATH not set
- Circular imports
- Missing dependencies

**Solutions**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pip install -r requirements.txt
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Checklist for New Tests

- [ ] Test is properly categorized with markers
- [ ] Test has descriptive name
- [ ] Test has docstring
- [ ] Uses fixtures from conftest.py
- [ ] Tests both success and failure paths
- [ ] Uses appropriate mocking
- [ ] Has clear assertions
- [ ] Is independent (no shared state)
- [ ] Runs quickly (< 1s for unit tests)
- [ ] Adds to coverage

## Code Review Checklist

- [ ] Tests cover new functionality
- [ ] Tests cover edge cases
- [ ] Tests are well-documented
- [ ] No duplicate test code
- [ ] Appropriate use of mocks
- [ ] Tests are deterministic
- [ ] Coverage increased
- [ ] Performance tests for critical paths
