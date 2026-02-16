import logging
import asyncio
import time
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache, TgAccount, Student
from services.hemis_service import HemisService
from bot import bot

logger = logging.getLogger(__name__)


/*
BACKGROUND SERVICES DISABLED FOR SECURITY (STATELESS TOKEN MODE)
*/
# async def sync_all_students_weekly_schedule():
#     """
#     Fetches schedule for ALL active students for the current week.
#     Scheduled to run: Monday 06:00.
#     """
#     pass
# 
# async def run_lesson_reminders():
#     """
#     # Checks cached weekly schedule for lessons starting SOON (10 mins msg warning).
#     # Scheduled to run at: 08:20, 09:50, 11:40, 13:20, 14:50, 16:20
#     """
#     pass
