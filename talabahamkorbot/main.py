import logging
import uvicorn
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, Response
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application # We use this adapter for aiogram
from aiogram.types import Update

from bot import bot, dp, BOT_ID
from config import WEBHOOK_URL, BOT_TOKEN
from database.db_connect import engine, create_tables, AsyncSessionLocal
from handlers import setup_routers
from utils.logging_config import setup_logging
from api.tutor import router as tutor_router

# Middlewares
from middlewares.db import DbSessionMiddleware
from middlewares.subscription import SubscriptionMiddleware
from middlewares.activity import ActivityMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware # NEW

# --- SECURITY ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from secure import Secure

# Logging setup
setup_logging()
logger = logging.getLogger(__name__)

# --- SECURITY CONFIG ---
# 1. Rate Limiting
# limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
from api.security import limiter

# 2. Secure Headers
secure_headers = Secure.with_default_headers()

# 3. Audit Logging
async def audit_logger(request: Request, response: Response, execution_time: float):
    # Only log state-changing methods or specific paths
    if request.method in ["POST", "PUT", "DELETE", "PATCH"] or "auth" in request.url.path:
        # Avoid logging large bodies or passwords
        # Just log metadata
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Try to get user_id if authenticated (this runs after request processed)
        # Note: Auth middleware usually sets user in state, but depends on impl.
        # Ideally, we'd have a standard AuditMiddleware class, but simple logging here works for now.
        
        log_entry = (
            f"AUDIT | {datetime.now()} | {client_ip} | {request.method} {request.url.path} "
            f"| Status: {response.status_code} | Time: {execution_time:.4f}s | UA: {user_agent}"
        )
        
        # Write to separate audit log file
        with open("audit.log", "a") as f:
            f.write(log_entry + "\n")

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
    
    # API Routers
    app.include_router(tutor_router)
    
    if MODE == "POLLING":
        logger.info("🔄 Starting Polling in Background...")
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot))
    else:
        try:
            # Check current webhook info to avoid flood control and redundant resets
            info = await bot.get_webhook_info()
            if info.url != WEBHOOK_URL:
                logger.info(f"🌐 Setting Webhook to: {WEBHOOK_URL}")
                await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
            else:
                logger.info("✅ Webhook already correctly set.")
        except Exception as e:
            logger.warning(f"⚠️ Webhook check/setup failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await bot.session.close()

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import Student
from sqlalchemy import select

scheduler = AsyncIOScheduler()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter # Register limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- MIDDLEWARES ---
app.add_middleware(SlowAPIMiddleware) # Rate Limiting
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["127.0.0.1"]) # Support X-Forwarded-Proto

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 1. Process Request
    response = await call_next(request)
    
    # 2. Add Security Headers
    secure_headers.set_headers(response)
    
    # 3. Audit Log
    process_time = time.time() - start_time
    await audit_logger(request, response, process_time)
    
    return response

# Celery Task Wrappers
from services.context_builder import run_daily_context_update
# from services.grade_checker import run_check_new_grades
from services.sync_service import run_sync_all_students
from services.election_service import ElectionService
from services.premium_service import run_premium_checker

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
    # from services.reminder_service import run_lesson_reminders, sync_all_students_weekly_schedule
    
    # 1. Weekly Sync (Monday 06:00)
    # scheduler.add_job(sync_all_students_weekly_schedule, 'cron', day_of_week='mon', hour=6, minute=0)
    
    # 2. Daily Reminders (Specific Times: 08:20, 09:50, 11:40, 13:20, 14:50, 16:20)
    reminder_times = ["08:20", "09:50", "11:40", "13:20", "14:50", "16:20"]
    #     h, m = map(int, rt.split(":"))
    #     scheduler.add_job(run_lesson_reminders, 'cron', hour=h, minute=m)
    
    # [NEW] Premium Expiry & Grace Period Checker (Daily 00:10)
    # scheduler.add_job(run_premium_checker, 'cron', hour=0, minute=10)
    
    # scheduler.start()
    logger.info("⏰ Background Task Scheduler DISABLED by User Request")

    # [NEW] Banner Analytics Flush (Buffer Optimization)
    from services.banner_analytics import BannerAnalyticsService
    
    async def flush_banner_analytics_loop():
        while True:
            await asyncio.sleep(60) # Every 60 seconds
            try:
                await BannerAnalyticsService().flush()
            except Exception as e:
                logger.error(f"Banner flush error: {e}")

    # Start independent loop
    asyncio.create_task(flush_banner_analytics_loop())


# ============================================================
#   BOT HANDLER (WEBHOOK)
# ============================================================

# Middlewares Order: DB -> Activity -> Subscription
dp.update.outer_middleware(DbSessionMiddleware())
# dp.update.middleware(ActivityMiddleware())
# dp.update.middleware(SubscriptionMiddleware())

# Root is now handled in api/oauth.py to support Hemis Callback
# @app.get("/")
# async def root():
#    return {"status": "active", "service": "TalabaHamkor API", "version": "1.0.0"}

@app.post("/webhook/bot")
async def bot_webhook(request: Request):
    """Feed update to aiogram"""
    if MODE == "WEBHOOK":
        try:
            body = await request.json()
            
            # [DEBUG] Log everything
            import json
            # [DEBUG] Log payload (Non-blocking via standard logger)
            logger.info(f"🔥 WEBHOOK HIT: {json.dumps(body)}")

            

            if "callback_query" in body:
                logger.info(f"🔍 Callback: {body['callback_query'].get('data')}")
            elif "message" in body:
                msg_text = body['message'].get('text')
                if msg_text:
                    logger.info(f"🔍 Message: {msg_text[:50]}")
            
            update = Update.model_validate(body, context={"bot": bot})
            await dp.feed_update(bot, update, bot_id=BOT_ID)
        except Exception as e:
            import traceback
            with open("/tmp/aiogram_error.log", "a") as f:
                f.write(f"\n--- ERROR {datetime.now()} ---\n")
                f.write(traceback.format_exc())
            logger.error(f"Webhook update processing failed: {e}")
            # return {"ok": True} anyway to stop Telegram from retrying failed/old updates endlessly
            return {"ok": True}
    return {"ok": True}

from api import router as api_router
from api.oauth import authlog_router
from api.student import router as student_router
from api.announcements import router as announcements_router
from fastapi.staticfiles import StaticFiles

app.include_router(api_router, prefix="/api/v1")
app.include_router(authlog_router) # Support callback paths like /authlog and /oauth/login
app.include_router(announcements_router, prefix="/api/v1")

from api.security_rsa import router as security_rsa_router
app.include_router(security_rsa_router, prefix="/api/v1")

from api.support import router as support_router
app.include_router(support_router, prefix="/api")

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
    # Increased workers to 4 to prevent concurrency bottlenecks (e.g. during slow HEMIS or aggregate queries)
    # [REVERTED] 1 Worker caused App Disconnection (Performance Bottleneck). Back to 4.
    # [FIX] Increase Keep-Alive to 75s to prevent "Connection Closed" errors on mobile NAT.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=4, timeout_keep_alive=75)
