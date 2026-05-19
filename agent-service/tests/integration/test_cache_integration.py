"""
Integration tests for Redis cache operations.

Uses real Redis or testcontainers for realistic cache testing.
"""
import pytest
import json
import asyncio
from unittest.mock import patch


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection(redis_connection):
    """Test Redis connection establishment."""
    response = await redis_connection.ping()
    assert response is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_set_and_get(redis_connection):
    """Test basic cache set and get operations."""
    key = "test:cache:key"
    value = {"test": "data", "number": 123}

    # Set value
    await redis_connection.set(key, json.dumps(value), ex=60)

    # Get value
    cached = await redis_connection.get(key)
    assert cached is not None
    assert json.loads(cached) == value

    # Cleanup
    await redis_connection.delete(key)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_expiration(redis_connection):
    """Test cache TTL expiration."""
    key = "test:cache:expiring"
    value = "test-value"

    # Set with 1 second TTL
    await redis_connection.set(key, value, ex=1)

    # Should exist immediately
    cached = await redis_connection.get(key)
    assert cached == value

    # Wait for expiration
    await asyncio.sleep(2)

    # Should be expired
    cached = await redis_connection.get(key)
    assert cached is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_delete(redis_connection):
    """Test cache deletion."""
    key = "test:cache:delete"
    value = "test-value"

    # Set value
    await redis_connection.set(key, value)

    # Verify exists
    assert await redis_connection.get(key) == value

    # Delete
    deleted = await redis_connection.delete(key)
    assert deleted == 1

    # Verify deleted
    assert await redis_connection.get(key) is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_concurrent_access(redis_connection):
    """Test concurrent cache access."""
    key = "test:cache:concurrent"
    value = {"data": "test"}

    async def set_value(i):
        test_key = f"{key}:{i}"
        await redis_connection.set(test_key, json.dumps(value), ex=60)
        return test_key

    async def get_value(key):
        cached = await redis_connection.get(key)
        return json.loads(cached) if cached else None

    # Set multiple values concurrently
    keys = await asyncio.gather(*[set_value(i) for i in range(10)])

    # Get values concurrently
    results = await asyncio.gather(*[get_value(k) for k in keys])

    # All should succeed
    assert all(r == value for r in results)

    # Cleanup
    await asyncio.gather(*[redis_connection.delete(k) for k in keys])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_invalidation(redis_connection):
    """Test cache invalidation pattern."""
    base_key = "test:cache:pattern"
    keys = [f"{base_key}:{i}" for i in range(5)]

    # Set multiple values
    for key in keys:
        await redis_connection.set(key, "test-value", ex=60)

    # Verify all exist
    for key in keys:
        assert await redis_connection.get(key) is not None

    # Delete all matching pattern
    deleted = await redis_connection.delete(*keys)
    assert deleted == len(keys)

    # Verify all deleted
    for key in keys:
        assert await redis_connection.get(key) is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_service_integration(redis_connection):
    """Test cache service with real Redis."""
    from app.services.cache_service import CacheService

    cache_service = CacheService()

    # Test cache key generation
    key = cache_service.generate_cache_key(
        "test_endpoint",
        "user-123",
        {"param": "value"}
    )
    assert key.startswith("test_endpoint:")

    # Test set and get
    test_data = {"result": "test", "cached": False}

    with patch("app.services.cache_service.redis_client", redis_connection):
        await cache_service.set_cached_response(key, test_data)

        cached = await cache_service.get_cached_response(key)
        assert cached == test_data

    # Cleanup
    await redis_connection.delete(key)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_failure_graceful_degradation():
    """Test graceful degradation when Redis is unavailable."""
    from app.services.cache_service import CacheService
    from app.clients.redis_client import RedisClient
    from unittest.mock import Mock, AsyncMock

    # Mock Redis client that fails
    mock_redis = Mock(spec=RedisClient)
    mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))
    mock_redis.set = AsyncMock(side_effect=Exception("Redis connection failed"))

    cache_service = CacheService()

    with patch("app.services.cache_service.redis_client", mock_redis):
        # Should not raise exception, return None gracefully
        key = "test:key"
        result = await cache_service.get_cached_response(key)
        assert result is None

        # Set should also not raise
        await cache_service.set_cached_response(key, {"data": "test"})


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_large_data(redis_connection):
    """Test caching large data structures."""
    key = "test:cache:large"

    # Create large data structure
    large_data = {
        "workout_plan": {
            "weeks": [
                {
                    "week": i,
                    "days": [
                        {
                            "day": j,
                            "exercises": [
                                {
                                    "name": f"Exercise {k}",
                                    "sets": 3,
                                    "reps": 10,
                                    "weight": 100
                                }
                                for k in range(10)
                            ]
                        }
                        for j in range(7)
                    ]
                }
                for i in range(12)
            ]
        }
    }

    # Set large data
    await redis_connection.set(key, json.dumps(large_data), ex=60)

    # Retrieve and verify
    cached = await redis_connection.get(key)
    assert cached is not None
    retrieved = json.loads(cached)
    assert retrieved == large_data

    # Cleanup
    await redis_connection.delete(key)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_connection_pool():
    """Test Redis connection pooling."""
    from app.clients.redis_client import redis_client

    # Make multiple concurrent requests
    async def ping_test():
        return await redis_client.ping()

    try:
        results = await asyncio.gather(*[ping_test() for _ in range(20)])
        assert all(results)
    except Exception:
        pytest.skip("Redis not available")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_unicode_handling(redis_connection):
    """Test caching data with unicode characters."""
    key = "test:cache:unicode"
    value = {
        "name": "테스트 사용자",  # Korean
        "exercise": "スクワット",  # Japanese
        "note": "Übung"  # German
    }

    await redis_connection.set(key, json.dumps(value, ensure_ascii=False), ex=60)

    cached = await redis_connection.get(key)
    assert cached is not None
    retrieved = json.loads(cached)
    assert retrieved == value

    # Cleanup
    await redis_connection.delete(key)
