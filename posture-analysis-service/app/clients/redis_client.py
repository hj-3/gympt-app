import redis.asyncio as redis
import json
import logging
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for pub/sub and caching."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection."""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password if settings.redis_password else None,
                db=settings.redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.client = None
    
    async def ping(self) -> bool:
        """Check Redis connection."""
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to Redis channel."""
        if not self.client:
            return 0
        
        try:
            return await self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis publish failed: {e}")
            return 0
    
    async def subscribe(self, *channels):
        """Subscribe to Redis channels."""
        if not self.client:
            return None
        
        try:
            self.pubsub = self.client.pubsub()
            await self.pubsub.subscribe(*channels)
            return self.pubsub
        except Exception as e:
            logger.error(f"Redis subscribe failed: {e}")
            return None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis."""
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value)
            await self.client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.pubsub:
            await self.pubsub.close()
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")


# Singleton instance
redis_client = RedisClient()
