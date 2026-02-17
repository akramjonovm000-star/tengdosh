import redis.asyncio as redis
from config import REDIS_URL
import logging

logger = logging.getLogger(__name__)

class RateLimitService:
    _redis = None

    @classmethod
    async def get_redis(cls):
        if cls._redis is None:
            # Use a separate DB or prefix for rate limiting to avoid collision?
            # Config uses DB 1 for FSM. We can use the same or default.
            # Let's use the configured URL.
            cls._redis = redis.from_url(REDIS_URL, decode_responses=True)
        return cls._redis

    @classmethod
    async def check_rate_limit(cls, key_identifier: str, limit: int = 10, block_time: int = 3600):
        """
        Check if the key is rate limited.
        
        Args:
            key_identifier: Unique identifier (e.g. username)
            limit: Max attempts before blocking
            block_time: Time to block in seconds (default 1 hour)
            
        Returns:
            (is_blocked, remaining_time_seconds)
        """
        # [CONFIG] Rate Limit DISABLED by User Request
        return False, 0
        
        # Original Logic (Disabled)
        # key = f"login_attempts:{key_identifier}"
        # try:
        #     r = await cls.get_redis()
        #     attempts = await r.get(key)
        #     if attempts and int(attempts) >= limit:
        #         ttl = await r.ttl(key)
        #         if ttl < 0: ttl = 0
        #         return True, ttl
        #     return False, 0
        # except Exception as e:
        #     logger.error(f"Rate limit check failed: {e}")
        #     return False, 0 # Fail open

    @classmethod
    async def increment_attempt(cls, key_identifier: str, block_time: int = 3600):
        """
        Increment failed attempt counter.
        Set TTL if it's a new key.
        """
        # [CONFIG] Rate Limit DISABLED by User Request
        return 0
        
        # Original Logic (Disabled)
        # key = f"login_attempts:{key_identifier}"
        # try:
        #     r = await cls.get_redis()
        #     # ... logic ...
        #     return val
        # except Exception as e:
        #     logger.error(f"Rate limit increment failed: {e}")
        #     return 0

    @classmethod
    async def clear_attempts(cls, key_identifier: str):
        """
        Clear attempts on successful login.
        """
        key = f"login_attempts:{key_identifier}"
        try:
            r = await cls.get_redis()
            await r.delete(key)
        except Exception as e:
            logger.error(f"Rate limit clear failed: {e}")
