import aioredis
from typing import Optional
from .config import settings
import logging
import json

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            await self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set value in Redis with optional TTL"""
        try:
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")

    async def delete(self, key: str):
        """Delete key from Redis"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")

    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: dict, ttl: Optional[int] = None):
        """Set JSON value in Redis"""
        await self.set(key, json.dumps(value), ttl)

redis_client = RedisClient()
