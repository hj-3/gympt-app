"""
Performance tests for Bedrock API calls.

Tests concurrent requests, response time distribution, and rate limiting.
"""
import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_bedrock_requests_10(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test 10 concurrent Bedrock requests."""
    from app.services.agent_service import agent_service

    async def make_request():
        return await agent_service.generate_workout_plan(
            user_id=f"user-{time.time()}",
            workout_request={
                "goal": "muscle_gain",
                "fitness_level": "intermediate",
                "days_per_week": 4,
                "equipment_available": ["barbell"]
            }
        )

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        start_time = time.time()

        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time

        # All should succeed
        assert all(not isinstance(r, Exception) for r in results)

        # Should complete in reasonable time
        assert duration < 10.0  # 10 seconds max

        print(f"\n10 concurrent requests completed in {duration:.2f}s")


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_bedrock_requests_50(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test 50 concurrent Bedrock requests."""
    from app.services.agent_service import agent_service

    async def make_request(i):
        return await agent_service.generate_workout_plan(
            user_id=f"user-{i}",
            workout_request={
                "goal": "muscle_gain",
                "fitness_level": "intermediate",
                "days_per_week": 4,
                "equipment_available": ["barbell"]
            }
        )

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        start_time = time.time()

        # Make 50 concurrent requests
        tasks = [make_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time

        # Count successes
        successes = sum(1 for r in results if not isinstance(r, Exception))

        # Most should succeed
        assert successes >= 45  # At least 90% success rate

        print(f"\n50 concurrent requests: {successes} succeeded in {duration:.2f}s")


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_response_time_distribution(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test response time distribution (P50, P95, P99)."""
    from app.services.agent_service import agent_service
    import statistics

    # Add realistic latency to mock
    async def mock_with_latency(*args, **kwargs):
        await asyncio.sleep(0.1)  # 100ms simulated latency
        return {
            "content": "Mock response",
            "model": "mock-model",
            "usage": {"input_tokens": 100, "output_tokens": 200},
            "stop_reason": "end_turn"
        }

    mock_bedrock_client.invoke_model = AsyncMock(side_effect=mock_with_latency)

    response_times = []

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # Make 100 requests
        for i in range(100):
            start = time.time()

            await agent_service.generate_workout_plan(
                user_id=f"user-{i}",
                workout_request={
                    "goal": "muscle_gain",
                    "fitness_level": "intermediate",
                    "days_per_week": 4
                },
                use_cache=False  # Disable cache for consistent timing
            )

            response_times.append(time.time() - start)

    # Calculate percentiles
    response_times.sort()
    p50 = response_times[49]  # 50th percentile
    p95 = response_times[94]  # 95th percentile
    p99 = response_times[98]  # 99th percentile

    print(f"\nResponse time distribution:")
    print(f"P50: {p50*1000:.2f}ms")
    print(f"P95: {p95*1000:.2f}ms")
    print(f"P99: {p99*1000:.2f}ms")

    # Assertions
    assert p50 < 0.5  # P50 under 500ms
    assert p95 < 1.0  # P95 under 1s
    assert p99 < 2.0  # P99 under 2s


@pytest.mark.performance
@pytest.mark.asyncio
async def test_no_memory_leaks(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test for memory leaks during sustained load."""
    from app.services.agent_service import agent_service
    import tracemalloc

    tracemalloc.start()

    async def make_requests(count):
        tasks = []
        for i in range(count):
            task = agent_service.generate_workout_plan(
                user_id=f"user-{i}",
                workout_request={
                    "goal": "muscle_gain",
                    "fitness_level": "intermediate",
                    "days_per_week": 4
                }
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # Baseline memory
        await make_requests(10)
        baseline = tracemalloc.get_traced_memory()[0]

        # More requests
        await make_requests(50)
        after = tracemalloc.get_traced_memory()[0]

        tracemalloc.stop()

        # Memory growth should be reasonable
        growth = (after - baseline) / baseline
        print(f"\nMemory growth: {growth*100:.2f}%")

        # Allow up to 50% growth for 5x requests
        assert growth < 0.5


@pytest.mark.performance
@pytest.mark.benchmark
def test_cache_key_generation_performance(benchmark):
    """Benchmark cache key generation performance."""
    from app.services.cache_service import CacheService

    service = CacheService()

    request = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4,
        "equipment_available": ["barbell", "dumbbell", "bench"],
        "injuries_or_limitations": "None"
    }

    # Benchmark key generation
    result = benchmark(
        service.generate_cache_key,
        "workout_recommend",
        "user-123",
        request
    )

    assert result is not None


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cache_vs_non_cache_performance(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Compare performance of cached vs non-cached requests."""
    from app.services.agent_service import agent_service
    import json

    # Setup cache with data
    cached_response = {
        "recommendation": "Cached workout",
        "model_used": "cached-model",
        "cached": False,
        "interaction_id": "cached-id"
    }

    request = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # Test cache miss
        mock_redis_client.get.return_value = None

        start = time.time()
        await agent_service.generate_workout_plan("user-123", request, use_cache=True)
        cache_miss_time = time.time() - start

        # Test cache hit
        mock_redis_client.get.return_value = json.dumps(cached_response)

        start = time.time()
        await agent_service.generate_workout_plan("user-123", request, use_cache=True)
        cache_hit_time = time.time() - start

        print(f"\nCache miss: {cache_miss_time*1000:.2f}ms")
        print(f"Cache hit: {cache_hit_time*1000:.2f}ms")
        print(f"Speedup: {cache_miss_time/cache_hit_time:.2f}x")

        # Cache hit should be faster
        assert cache_hit_time < cache_miss_time


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_sustained_load_100_requests(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test sustained load with 100 sequential requests."""
    from app.services.agent_service import agent_service

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        start_time = time.time()
        errors = 0

        for i in range(100):
            try:
                await agent_service.generate_workout_plan(
                    user_id=f"user-{i}",
                    workout_request={
                        "goal": "muscle_gain",
                        "fitness_level": "intermediate",
                        "days_per_week": 4
                    }
                )
            except Exception:
                errors += 1

        duration = time.time() - start_time

        print(f"\n100 requests completed in {duration:.2f}s")
        print(f"Throughput: {100/duration:.2f} req/s")
        print(f"Errors: {errors}")

        # Should have low error rate
        assert errors < 5  # Less than 5% error rate


@pytest.mark.performance
@pytest.mark.asyncio
async def test_api_endpoint_performance(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test API endpoint response time."""
    request = {
        "user_id": "test-user",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4
    }

    response_times = []

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        for _ in range(20):
            start = time.time()
            response = test_client.post("/agent/workout/recommend", json=request)
            response_times.append(time.time() - start)

            assert response.status_code == 200

    avg_time = sum(response_times) / len(response_times)
    print(f"\nAverage API response time: {avg_time*1000:.2f}ms")

    # API should respond quickly
    assert avg_time < 1.0  # Under 1 second average
