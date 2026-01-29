import asyncio
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal, engine, Base
from database.models import SubscriptionPlan, SubscriptionPurchase # Ensure they are imported so Base knows them

async def main():
    async with engine.begin() as conn:
        # 1. Create new tables
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created (if not existed).")
        
        # 2. Add 'trial_used' column if missing (PostgreSQL fallback)
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS trial_used BOOLEAN DEFAULT FALSE"))
            print("Columns added (if missing).")
        except Exception as e:
            print(f"Column addition error: {e}")
            
    print("Database initialization finished.")

if __name__ == "__main__":
    asyncio.run(main())
