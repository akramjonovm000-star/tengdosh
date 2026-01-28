import logging
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application # We use this adapter for aiogram
from aiogram.types import Update

from bot import bot, dp
from config import WEBHOOK_URL, BOT_TOKEN
from database.db_connect import engine, create_tables, AsyncSessionLocal
from handlers import setup_routers
from utils.logging_config import setup_logging

# Middlewares
from middlewares.db import DbSessionMiddleware
from middlewares.subscription import SubscriptionMiddleware
from middlewares.activity import ActivityMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware # NEW

# Logging setup
setup_logging()
logger = logging.getLogger(__name__)

# ============================================================
#   LIFECYCLE
# ============================================================
# ============================================================
#   LIFECYCLE (WEBHOOK MODE)
# ============================================================
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 Starting up ({MODE} Mode)...")
    
    # Init Cache (Use InMemory to avoid Redis dependency issues)
    from fastapi_cache.backends.inmemory import InMemoryBackend
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    
    # Initialize Firebase Push Notifications
    from services.notification_service import NotificationService
    NotificationService.initialize()
    
    await create_tables()
    
    # Setup routers
    root_router = setup_routers()
    # Check if router is already registered to avoid duplicates
    if root_router not in dp.sub_routers:
        dp.include_router(root_router)
    
    if MODE == "POLLING":
        logger.info("🔄 Starting Polling in Background...")
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot))
    else:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await bot.session.close()

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import Student
from sqlalchemy import select

scheduler = AsyncIOScheduler()

app = FastAPI(lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["127.0.0.1"]) # NEW: Support X-Forwarded-Proto

# Celery Task Wrappers
from services.context_builder import run_daily_context_update
from services.grade_checker import run_check_new_grades
from services.sync_service import run_sync_all_students

@app.on_event("startup")
async def start_scheduler():
    # scheduler.add_job(lambda: run_daily_context_update.delay(), 'cron', hour=22, minute=30)
    
    attendance_times = [
        (4, 55),
        (6, 25),
        (7, 55),
        (9, 55),
        (11, 25),
        (12, 55),
    ]
    
    # for h, m in attendance_times:
    #     scheduler.add_job(lambda: run_sync_all_students.delay(), 'cron', hour=h, minute=m)

    # scheduler.add_job(lambda: run_check_new_grades.delay(), 'interval', minutes=30)
    
    # [NEW] Lesson Reminder System
    from services.reminder_service import run_lesson_reminders, sync_all_students_weekly_schedule
    
    # 1. Weekly Sync (Monday 06:00)
    # scheduler.add_job(sync_all_students_weekly_schedule, 'cron', day_of_week='mon', hour=6, minute=0)
    
    # 2. Daily Reminders (Specific Times: 08:20, 09:50, 11:40, 13:20, 14:50, 16:20)
    reminder_times = ["08:20", "09:50", "11:40", "13:20", "14:50", "16:20"]
    # for rt in reminder_times:
    #     h, m = map(int, rt.split(":"))
    #     scheduler.add_job(run_lesson_reminders, 'cron', hour=h, minute=m)
        
    scheduler.start()
    logger.info("⏰ Background Task Scheduler Started (Celery + Fixed Reminders)")


# ============================================================
#   BOT HANDLER (WEBHOOK)
# ============================================================

dp.update.middleware(DbSessionMiddleware())
dp.message.middleware(ActivityMiddleware())
dp.callback_query.middleware(ActivityMiddleware())
dp.message.middleware(SubscriptionMiddleware())
dp.callback_query.middleware(SubscriptionMiddleware())

@app.get("/")
async def root():
    return {"status": "active", "service": "TalabaHamkor API", "version": "1.0.0"}

@app.post("/webhook/bot")
async def bot_webhook(request: Request):
    """Feed update to aiogram"""
    if MODE == "WEBHOOK":
        try:
            body = await request.json()
            # Diagnostic Log
            if "callback_query" in body:
                logger.info(f"🔍 Webhook Callback: {body['callback_query'].get('data')}")
            elif "message" in body:
                logger.info(f"🔍 Webhook Message: {body['message'].get('text')}")
                
            update = Update.model_validate(body, context={"bot": bot})
            await dp.feed_update(bot, update)
        except Exception as e:
            import traceback
            with open("/tmp/aiogram_error.log", "a") as f:
                f.write(f"\n--- ERROR {datetime.now()} ---\n")
                f.write(traceback.format_exc())
            logger.error(f"Webhook update processing failed: {e}")
            raise e
    return {"ok": True}

from api import router as api_router
from api.oauth import authlog_router
from fastapi.staticfiles import StaticFiles

app.include_router(authlog_router)
app.include_router(api_router, prefix="/api/v1")

import os
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
#   MAIN
# ============================================================
# ============================================================
#   MAIN
# ============================================================
import os
import asyncio

MODE = os.environ.get("BOT_MODE", "WEBHOOK")

if __name__ == "__main__":
    logger.info("🔥 Server starting (Universal Mode)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
