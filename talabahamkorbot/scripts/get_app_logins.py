
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import User, Student

async def get_login_stats():
    async with AsyncSessionLocal() as session:
        # 1. Total Users with Hemis Token (App Logins)
        total_app_users = await session.scalar(
            select(func.count(User.id)).where(User.hemis_token.isnot(None))
        )
        
        # 2. Total Students with Hemis Token
        total_students = await session.scalar(
            select(func.count(Student.id)).where(Student.hemis_token.isnot(None))
        )
        
        # 3. Recent Logins (Last 24h)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logins = await session.scalar(
            select(func.count(User.id)).where(User.updated_at >= yesterday)
        )
        
        print("-" * 30)
        print(f"APP LOGIN STATISTICS")
        print("-" * 30)
        print(f"Total Unique Logins: {total_app_users}")
        print(f"Total Students:      {total_students}")
        print(f"Active (Last 24h):   {recent_logins}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(get_login_stats())
