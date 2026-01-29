
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def clear_clubs():
    async with AsyncSessionLocal() as session:
        print("🗑 Tozalash boshlanmoqda...")
        
        # 1. Clear Memberships (Dependent table)
        await session.execute(text("DELETE FROM club_memberships"))
        print("✅ Klub a'zolari tozalandi.")
        
        # 2. Clear Clubs
        await session.execute(text("DELETE FROM clubs"))
        print("✅ Klublar tozalandi.")
        
        await session.commit()
        print("🎉 Barcha test klub ma'lumotlari o'chirildi!")

if __name__ == "__main__":
    asyncio.run(clear_clubs())
