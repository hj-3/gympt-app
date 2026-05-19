import pytest
from unittest.mock import AsyncMock, patch
from app.clients.redis_client import RedisClient


@pytest.mark.asyncio
async def test_cache_set_get():
    """Test Redis set and get operations."""
    client = RedisClient()
    
    # Mock Redis client
    with patch.object(client, 'client') as mock_redis:
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value='{"key": "value"}')
        
        # Set
        result = await client.set("test_key", {"key": "value"})
        assert result is True
        
        # Get
        value = await client.get("test_key")
        assert value == {"key": "value"}


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss scenario."""
    client = RedisClient()
    
    with patch.object(client, 'client') as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        
        value = await client.get("nonexistent_key")
        assert value is None


@pytest.mark.asyncio
async def test_cache_exists():
    """Test key existence check."""
    client = RedisClient()
    
    with patch.object(client, 'client') as mock_redis:
        mock_redis.exists = AsyncMock(return_value=1)
        
        exists = await client.exists("test_key")
        assert exists is True
