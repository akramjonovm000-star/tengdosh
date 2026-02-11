from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config import BOT_TOKEN, REDIS_URL


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)

# Use Redis Storage for FSM to support multiple workers
redis = Redis.from_url(REDIS_URL)
storage = RedisStorage(redis=redis)

dp = Dispatcher(storage=storage)
