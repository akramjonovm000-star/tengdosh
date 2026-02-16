import asyncio
from config import REDIS_URL
import redis.asyncio as redis

async def test_redis():
    print(f"Testing Redis URL: {REDIS_URL}")
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        await r.ping()
        print("Redis connection successful!")
        await r.close()
    except Exception as e:
        print(f"Redis connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis())
