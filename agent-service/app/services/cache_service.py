import hashlib
import json
import logging
from typing import Any, Optional, Dict
from app.clients.redis_client import redis_client
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing Redis caching with smart key generation."""

    def __init__(self):
        self.default_ttl = settings.redis_cache_ttl

    def generate_cache_key(
        self,
        endpoint: str,
        user_id: str,
        request_data: Dict[str, Any]
    ) -> str:
        """
        Generate a smart cache key based on endpoint, user, and request.

        Args:
            endpoint: API endpoint name
            user_id: User identifier
            request_data: Request parameters

        Returns:
            Cache key string
        """
        # Create deterministic hash of request data
        request_str = json.dumps(request_data, sort_keys=True)
        request_hash = hashlib.md5(request_str.encode()).hexdigest()[:8]

        cache_key = f"{endpoint}:{user_id}:{request_hash}"
        return cache_key

    async def get_cached_response(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response from Redis.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if not found
        """
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit: {cache_key}")
                return cached_data
            else:
                logger.debug(f"Cache miss: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None

    async def set_cached_response(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store response in Redis cache.

        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (defaults to configured TTL)

        Returns:
            True if successful, False otherwise
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            success = await redis_client.set(cache_key, data, ttl=ttl)
            if success:
                logger.info(f"Cached response: {cache_key} (TTL: {ttl}s)")
            return success

        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False

    async def invalidate_cache(
        self,
        cache_key: str
    ) -> bool:
        """
        Invalidate a cache entry.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await redis_client.delete(cache_key)
            if success:
                logger.info(f"Invalidated cache: {cache_key}")
            return success

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False

    async def check_cache_exists(
        self,
        cache_key: str
    ) -> bool:
        """
        Check if cache key exists.

        Args:
            cache_key: Cache key to check

        Returns:
            True if exists, False otherwise
        """
        try:
            return await redis_client.exists(cache_key)
        except Exception as e:
            logger.error(f"Cache existence check error: {e}")
            return False

    async def delete_cached_response(
        self,
        cache_key: str
    ) -> int:
        """
        Delete cached response (alias for invalidate_cache).

        Args:
            cache_key: Cache key to delete

        Returns:
            Number of keys deleted
        """
        try:
            deleted = await redis_client.delete(cache_key)
            return deleted
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return 0

    async def invalidate_user_cache(
        self,
        user_id: str,
        endpoint: Optional[str] = None
    ) -> int:
        """
        Invalidate all cache entries for a user.

        Args:
            user_id: User identifier
            endpoint: Optional endpoint filter

        Returns:
            Number of keys deleted
        """
        try:
            pattern = f"{endpoint}:{user_id}:*" if endpoint else f"*:{user_id}:*"
            keys = await redis_client.keys(pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries for user {user_id}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"User cache invalidation error: {e}")
            return 0


# Singleton instance
cache_service = CacheService()
