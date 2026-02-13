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
        r = await cls.get_redis()
        key = f"login_attempts:{key_identifier}"
        
        try:
            attempts = await r.get(key)
            if attempts and int(attempts) >= limit:
                ttl = await r.ttl(key)
                if ttl < 0: ttl = 0
                return True, ttl
            
            return False, 0
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False, 0 # Fail open if Redis is down

    @classmethod
    async def increment_attempt(cls, key_identifier: str, block_time: int = 3600):
        """
        Increment failed attempt counter.
        Set TTL if it's a new key.
        """
        r = await cls.get_redis()
        key = f"login_attempts:{key_identifier}"
        
        try:
            # pipeline for atomicity-ish (not strict here but good enough)
            pipe = r.pipeline()
            pipe.incr(key)
            # We want to set TTL on the FIRST increment, or refresh it?
            # Usually we want a rolling window or fixed window. 
            # Plan says: "If new key, set TTL".
            # If we just incr, TTL is -1 (persistent). 
            # Let's check TTL first or just expire if new.
            
            # Simple approach:
            # If key didn't exist, set expire.
            # If key exists, keep existing TTL? Or extend?
            # Security-wise: If I try once every hour, I should strictly be cleared.
            # If I try 10 times rapidly, I get blocked.
            
            # Better approach for "Block 1 hour after 10 fails":
            # The count should persist for some time (e.g. 1 hour window).
            # If count hits 10, we ensure TTL is at least block_time.
            
            val = await r.incr(key)
            if val == 1:
                # First attempt, start the window (e.g. 1 hour to accumulate 10 fails?)
                # Or just keep it for block_time?
                await r.expire(key, block_time)
            
            elif val >= 10:
                 # If we just hit the limit, ensure we block for the full duration
                 # Or just let the existing TTL run out?
                 # User asked: "after 10 attempts... system temporarily blocks... try again after an hour"
                 # This implies the block STARTS when limit is hit.
                 if val == 10:
                     await r.expire(key, block_time)
            
            return val
        except Exception as e:
            logger.error(f"Rate limit increment failed: {e}")
            return 0

    @classmethod
    async def clear_attempts(cls, key_identifier: str):
        """
        Clear attempts on successful login.
        """
        r = await cls.get_redis()
        key = f"login_attempts:{key_identifier}"
        try:
            await r.delete(key)
        except Exception as e:
            logger.error(f"Rate limit clear failed: {e}")
