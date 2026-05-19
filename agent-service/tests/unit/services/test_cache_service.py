"""
Unit tests for CacheService.

Tests cache key generation, TTL handling, and cache operations.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import hashlib
import json


@pytest.mark.unit
def test_cache_key_generation():
    """Test cache key generation is deterministic."""
    from app.services.cache_service import CacheService

    service = CacheService()

    # Same inputs should generate same key
    key1 = service.generate_cache_key(
        "workout_recommend",
        "user-123",
        {"goal": "muscle_gain", "level": "intermediate"}
    )

    key2 = service.generate_cache_key(
        "workout_recommend",
        "user-123",
        {"goal": "muscle_gain", "level": "intermediate"}
    )

    assert key1 == key2


@pytest.mark.unit
def test_cache_key_different_for_different_inputs():
    """Test cache keys are different for different inputs."""
    from app.services.cache_service import CacheService

    service = CacheService()

    key1 = service.generate_cache_key(
        "workout_recommend",
        "user-123",
        {"goal": "muscle_gain"}
    )

    key2 = service.generate_cache_key(
        "workout_recommend",
        "user-456",
        {"goal": "muscle_gain"}
    )

    key3 = service.generate_cache_key(
        "workout_recommend",
        "user-123",
        {"goal": "weight_loss"}
    )

    assert key1 != key2
    assert key1 != key3
    assert key2 != key3


@pytest.mark.unit
def test_cache_key_collision_resistance():
    """Test cache key generation is collision-resistant."""
    from app.services.cache_service import CacheService

    service = CacheService()

    # Generate many keys and check for collisions
    keys = set()
    for i in range(100):
        key = service.generate_cache_key(
            "endpoint",
            f"user-{i}",
            {"param": f"value-{i}"}
        )
        keys.add(key)

    # All keys should be unique
    assert len(keys) == 100


@pytest.mark.unit
def test_cache_key_format():
    """Test cache key format."""
    from app.services.cache_service import CacheService

    service = CacheService()

    key = service.generate_cache_key(
        "workout_recommend",
        "user-123",
        {"goal": "muscle_gain"}
    )

    # Key should start with endpoint name
    assert key.startswith("workout_recommend:")
    # Should contain hash
    assert len(key.split(":")[-1]) > 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cached_response():
    """Test getting cached response."""
    from app.services.cache_service import CacheService
    from unittest.mock import AsyncMock

    service = CacheService()

    mock_redis = Mock()
    cached_data = {"result": "cached"}
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

    with patch("app.services.cache_service.redis_client", mock_redis):
        result = await service.get_cached_response("test:key")

        assert result == cached_data
        mock_redis.get.assert_called_once_with("test:key")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cached_response_miss():
    """Test cache miss returns None."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.services.cache_service.redis_client", mock_redis):
        result = await service.get_cached_response("test:key")

        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_cached_response():
    """Test setting cached response."""
    from app.services.cache_service import CacheService
    from app.config import settings

    service = CacheService()

    mock_redis = Mock()
    mock_redis.set = AsyncMock(return_value=True)

    test_data = {"result": "test"}

    with patch("app.services.cache_service.redis_client", mock_redis):
        await service.set_cached_response("test:key", test_data)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args

        # Verify key and data
        assert call_args.args[0] == "test:key"
        assert json.loads(call_args.args[1]) == test_data

        # Verify TTL is set
        assert call_args.kwargs.get("ex") == settings.cache_ttl_seconds


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_cached_response_custom_ttl():
    """Test setting cached response with custom TTL."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    mock_redis.set = AsyncMock(return_value=True)

    with patch("app.services.cache_service.redis_client", mock_redis):
        await service.set_cached_response(
            "test:key",
            {"data": "test"},
            ttl=7200  # 2 hours
        )

        call_args = mock_redis.set.call_args
        assert call_args.kwargs.get("ex") == 7200


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cached_response_json_error():
    """Test handling of invalid JSON in cache."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    # Return invalid JSON
    mock_redis.get = AsyncMock(return_value="invalid json {")

    with patch("app.services.cache_service.redis_client", mock_redis):
        result = await service.get_cached_response("test:key")

        # Should return None on JSON decode error
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cached_response_redis_error():
    """Test handling of Redis connection error."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))

    with patch("app.services.cache_service.redis_client", mock_redis):
        result = await service.get_cached_response("test:key")

        # Should return None on error (graceful degradation)
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_cached_response_redis_error():
    """Test handling of Redis error on set."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    mock_redis.set = AsyncMock(side_effect=Exception("Redis connection failed"))

    with patch("app.services.cache_service.redis_client", mock_redis):
        # Should not raise exception (graceful degradation)
        await service.set_cached_response("test:key", {"data": "test"})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_cached_response():
    """Test deleting cached response."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    mock_redis.delete = AsyncMock(return_value=1)

    with patch("app.services.cache_service.redis_client", mock_redis):
        result = await service.delete_cached_response("test:key")

        assert result == 1
        mock_redis.delete.assert_called_once_with("test:key")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalidate_user_cache():
    """Test invalidating all cache entries for a user."""
    from app.services.cache_service import CacheService

    service = CacheService()

    mock_redis = Mock()
    # Mock pattern matching
    mock_redis.keys = AsyncMock(return_value=[
        "workout_recommend:user123:hash1",
        "workout_recommend:user123:hash2"
    ])
    mock_redis.delete = AsyncMock(return_value=2)

    with patch("app.services.cache_service.redis_client", mock_redis):
        deleted = await service.invalidate_user_cache("user123")

        # Should find and delete matching keys
        mock_redis.keys.assert_called_once()
        if deleted > 0:
            mock_redis.delete.assert_called()


@pytest.mark.unit
def test_cache_key_with_nested_dict():
    """Test cache key generation with nested dictionary."""
    from app.services.cache_service import CacheService

    service = CacheService()

    request = {
        "goal": "muscle_gain",
        "equipment": {
            "available": ["barbell", "dumbbell"],
            "preferred": "barbell"
        },
        "schedule": {
            "days": [1, 3, 5],
            "time": "morning"
        }
    }

    key = service.generate_cache_key("endpoint", "user-123", request)

    assert key is not None
    assert len(key) > 0


@pytest.mark.unit
def test_cache_key_deterministic_dict_order():
    """Test cache key is same regardless of dict key order."""
    from app.services.cache_service import CacheService

    service = CacheService()

    # Different order, same content
    request1 = {"a": 1, "b": 2, "c": 3}
    request2 = {"c": 3, "a": 1, "b": 2}

    key1 = service.generate_cache_key("endpoint", "user", request1)
    key2 = service.generate_cache_key("endpoint", "user", request2)

    # Keys should be identical (dict is sorted before hashing)
    assert key1 == key2
