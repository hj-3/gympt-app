# GYMPT Posture Analysis Service - Testing Guide

Comprehensive guide for writing and running tests for the posture analysis service.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Categories](#test-categories)
3. [Writing Tests](#writing-tests)
4. [WebSocket Testing](#websocket-testing)
5. [Performance Testing](#performance-testing)
6. [Creating Test Fixtures](#creating-test-fixtures)
7. [Mocking Strategies](#mocking-strategies)
8. [Best Practices](#best-practices)

## Testing Philosophy

### Test Pyramid

Our test suite follows the testing pyramid:

```
       /\
      /E2E\         - Few comprehensive end-to-end tests
     /------\
    /Integration\   - Moderate integration tests
   /------------\
  /  Unit Tests  \  - Many fast unit tests
 /----------------\
```

- **Unit Tests (70%)**: Fast, isolated, test single components
- **Integration Tests (20%)**: Test component interactions
- **E2E Tests (10%)**: Test complete user workflows

### Coverage Goals

- **Overall**: 80%+ coverage
- **Critical paths**: 95%+ coverage (rep counting, pose estimation)
- **Business logic**: 90%+ coverage (exercise rules, feedback)

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

**Example: Testing Rep Counter**

```python
def test_squat_rep_counting():
    counter = RepCounter(exercise_type="squat")
    
    # Test complete rep cycle
    keypoints_down = {"left_hip": {"x": 0.42, "y": 0.68}}
    keypoints_up = {"left_hip": {"x": 0.42, "y": 0.50}}
    
    counter.count_reps(keypoints_up)
    counter.count_reps(keypoints_down)
    counter.count_reps(keypoints_up)
    
    assert counter.total_reps >= 0
```

### 2. Integration Tests

Test interactions between components.

**Example: Testing DynamoDB Integration**

```python
async def test_dynamodb_logging(mock_dynamodb):
    from app.clients.dynamodb_client import DynamoDBClient
    
    client = DynamoDBClient()
    
    # Write event
    await client.log_event({
        "session_id": "test",
        "timestamp": time.time(),
        "event_type": "rep_completed"
    })
    
    # Verify written
    # (implementation specific)
```

### 3. E2E Tests

Test complete workflows end-to-end.

**Example: Full Squat Session**

```python
async def test_full_squat_session(test_client):
    with test_client.websocket_connect("/ws/posture/test") as ws:
        # Connect
        ws.receive_json()
        
        # Send frames
        for i in range(100):
            ws.send_json({"type": "frame", "frame": "...", "exercise": "squat"})
            analysis = ws.receive_json()
        
        # Verify session data
        # ...
```

## Writing Tests

### Basic Test Structure

```python
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestMyComponent:
    """Test suite for MyComponent."""
    
    @pytest.fixture
    def component(self):
        """Create component instance."""
        return MyComponent()
    
    async def test_basic_functionality(self, component):
        """Test basic functionality."""
        result = await component.do_something()
        assert result is not None
    
    async def test_edge_case(self, component):
        """Test edge case handling."""
        result = await component.handle_edge_case()
        assert result == expected_value
```

### Using Fixtures

Fixtures provide reusable test data and setup:

```python
@pytest.fixture
def sample_keypoints():
    """Generate sample keypoints."""
    return {
        "left_hip": {"x": 0.4, "y": 0.6, "confidence": 0.9},
        "right_hip": {"x": 0.6, "y": 0.6, "confidence": 0.9}
    }

def test_with_fixture(sample_keypoints):
    # Use the fixture
    result = analyze_keypoints(sample_keypoints)
    assert result is not None
```

### Parametrized Tests

Test multiple scenarios with one test:

```python
@pytest.mark.parametrize("exercise,expected_threshold", [
    ("squat", 0.15),
    ("pushup", 0.10),
    ("deadlift", 0.20),
])
def test_thresholds(exercise, expected_threshold):
    counter = RepCounter(exercise_type=exercise)
    assert counter.thresholds["down_threshold"] == expected_threshold
```

## WebSocket Testing

### Basic WebSocket Test

```python
async def test_websocket_connection(test_client):
    with test_client.websocket_connect("/ws/posture/test") as websocket:
        # Receive welcome
        data = websocket.receive_json()
        assert data["type"] == "connected"
        
        # Send message
        websocket.send_json({"type": "ping"})
        
        # Receive response
        response = websocket.receive_json()
        assert response["type"] == "pong"
```

### Testing Frame Processing

```python
async def test_frame_processing(test_client, base64_encoded_frame):
    with test_client.websocket_connect("/ws/posture/test") as websocket:
        websocket.receive_json()  # Welcome
        
        # Send frame
        websocket.send_json({
            "type": "frame",
            "frame": base64_encoded_frame,
            "exercise": "squat"
        })
        
        # Receive analysis
        analysis = websocket.receive_json()
        assert analysis["type"] == "analysis"
        assert "score" in analysis
        assert "issues" in analysis
```

### Testing Concurrent Connections

```python
async def test_concurrent_connections(test_client):
    websockets = []
    
    try:
        # Open multiple connections
        for i in range(10):
            ws = test_client.websocket_connect(f"/ws/posture/test-{i}")
            ws.__enter__()
            websockets.append(ws)
            ws.receive_json()  # Welcome
        
        # All should be connected
        assert len(websockets) == 10
        
    finally:
        # Cleanup
        for ws in websockets:
            ws.__exit__(None, None, None)
```

## Performance Testing

### Measuring Latency

```python
async def test_latency(test_client, base64_encoded_frame):
    import time
    import statistics
    
    latencies = []
    
    with test_client.websocket_connect("/ws/posture/perf") as websocket:
        websocket.receive_json()
        
        for _ in range(100):
            start = time.time()
            
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            websocket.receive_json()
            
            latency = time.time() - start
            latencies.append(latency)
    
    # Calculate percentiles
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    
    print(f"P50: {p50*1000:.1f}ms, P95: {p95*1000:.1f}ms")
    
    assert p95 < 0.5  # P95 latency < 500ms
```

### Measuring Throughput

```python
async def test_throughput(test_client, base64_encoded_frame):
    import time
    
    num_frames = 100
    
    with test_client.websocket_connect("/ws/posture/throughput") as websocket:
        websocket.receive_json()
        
        start = time.time()
        
        for _ in range(num_frames):
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            websocket.receive_json()
        
        elapsed = time.time() - start
        fps = num_frames / elapsed
        
        print(f"Throughput: {fps:.1f} FPS")
        
        assert fps >= 30  # Minimum 30 FPS
```

### Memory Testing

```python
async def test_memory_usage(test_client, base64_encoded_frame):
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    with test_client.websocket_connect("/ws/posture/memory") as websocket:
        websocket.receive_json()
        
        # Process many frames
        for _ in range(1000):
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            try:
                websocket.receive_json()
            except:
                pass
    
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    print(f"Memory increase: {memory_increase:.1f}MB")
    
    # Should not leak memory
    assert memory_increase < 100
```

## Creating Test Fixtures

### Image Fixtures

Place test images in `tests/fixtures/images/`:

```python
@pytest.fixture
def good_squat_image():
    """Load good squat form image."""
    image_path = Path(__file__).parent / "fixtures" / "images" / "good_squat.jpg"
    return cv2.imread(str(image_path))
```

### Landmark Fixtures

Use the LandmarkGenerator utility:

```python
from tests.utils.landmark_generator import LandmarkGenerator

@pytest.fixture
def squat_landmarks():
    """Generate squat landmarks."""
    gen = LandmarkGenerator()
    return gen.generate_squat_landmarks(depth=0.7)

@pytest.fixture
def rep_sequence():
    """Generate rep sequence."""
    gen = LandmarkGenerator()
    return gen.generate_rep_sequence("squat", num_reps=10)
```

### Video Fixtures

For video testing:

```python
@pytest.fixture
def squat_video_path():
    """Path to test squat video."""
    return Path(__file__).parent / "fixtures" / "videos" / "squat_10reps.mp4"
```

## Mocking Strategies

### Mock vs Real MediaPipe

For most tests, use mock estimator for speed:

```python
# Use mock (fast)
from app.pose_estimator.mock_estimator import MockPoseEstimator

estimator = MockPoseEstimator()
```

For integration tests with real pose estimation:

```python
# Use real MediaPipe (slower but accurate)
from app.pose_estimator.mediapipe_estimator import MediaPipeEstimator

estimator = MediaPipeEstimator(use_gpu=False)
```

### Mocking AWS Services

Use moto for AWS services:

```python
from moto import mock_aws
import boto3

@pytest.fixture
def mock_dynamodb():
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
        
        # Create table
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield dynamodb
```

### Mocking Redis

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def mock_redis():
    with patch('app.clients.redis_client.redis_client') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.publish = AsyncMock(return_value=1)
        yield mock
```

## Best Practices

### 1. Test Naming

Use descriptive names that explain what is being tested:

```python
# Good
def test_squat_rep_counter_increments_on_complete_rep():
    pass

# Bad
def test_counter():
    pass
```

### 2. Arrange-Act-Assert Pattern

Structure tests clearly:

```python
def test_example():
    # Arrange - Set up test data
    counter = RepCounter("squat")
    keypoints = {"left_hip": {"x": 0.4, "y": 0.6}}
    
    # Act - Perform action
    result = counter.count_reps(keypoints)
    
    # Assert - Verify outcome
    assert result.total_reps == 0
```

### 3. Single Assertion Focus

Each test should verify one behavior:

```python
# Good - Single focus
def test_rep_counter_starts_at_zero():
    counter = RepCounter("squat")
    assert counter.total_reps == 0

def test_rep_counter_increments():
    counter = RepCounter("squat")
    # ... do rep
    assert counter.total_reps == 1

# Avoid - Multiple unrelated assertions
def test_rep_counter():
    counter = RepCounter("squat")
    assert counter.total_reps == 0
    assert counter.current_state == RepState.STARTING
    assert counter.exercise_type == "squat"
```

### 4. Test Independence

Tests should not depend on each other:

```python
# Good - Independent
def test_first():
    counter = RepCounter("squat")
    # test logic

def test_second():
    counter = RepCounter("squat")  # Fresh instance
    # test logic

# Bad - Dependent
counter = RepCounter("squat")  # Shared state

def test_first():
    counter.total_reps = 1

def test_second():
    assert counter.total_reps == 1  # Depends on test_first
```

### 5. Use Custom Assertions

Create custom assertions for better error messages:

```python
from tests.utils.assertions import assert_rep_count

# Good - Clear error message
assert_rep_count(result, expected_reps=10, tolerance=1)

# Less clear
assert 9 <= result["total_reps"] <= 11
```

### 6. Clean Up Resources

Always clean up in tests:

```python
async def test_with_cleanup():
    resource = await create_resource()
    
    try:
        # Test logic
        result = await use_resource(resource)
        assert result is not None
    finally:
        # Always cleanup
        await resource.close()
```

### 7. Mark Slow Tests

Mark tests that take >1 second:

```python
@pytest.mark.slow
async def test_long_running_operation():
    # Long test
    pass
```

Run without slow tests:
```bash
pytest -m "not slow"
```

### 8. Skip Conditional Tests

Skip tests that require specific conditions:

```python
@pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU not available")
def test_gpu_feature():
    # GPU test
    pass
```

## Debugging Tests

### Print Debugging

```python
def test_with_debug(capsys):
    result = my_function()
    print(f"Result: {result}")
    
    captured = capsys.readouterr()
    # Can verify printed output
```

### Using pytest -s

Run with output:
```bash
pytest tests/test_file.py::test_name -s
```

### Using pdb

Add breakpoint:
```python
def test_debug():
    result = my_function()
    import pdb; pdb.set_trace()  # Debugger stops here
    assert result is not None
```

### Verbose Output

```bash
# Very verbose
pytest -vv

# Show local variables on failure
pytest -l

# Show test durations
pytest --durations=10
```

## Continuous Improvement

### Monitor Coverage

```bash
# Run with coverage
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html

# Focus on uncovered lines
pytest --cov=app --cov-report=term-missing
```

### Review Flaky Tests

If tests fail intermittently:

1. Add retries for network/timing issues
2. Increase timeouts for slow operations
3. Fix race conditions
4. Add proper synchronization

### Performance Benchmarking

Track performance over time:

```python
import pytest

def test_performance(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result is not None
```

---

For more information, see:
- [tests/README.md](README.md) - Test suite overview
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
