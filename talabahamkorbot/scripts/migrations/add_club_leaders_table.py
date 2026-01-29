
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        print("🔄 Migrating Club Leaders...")
        
        # 1. Create table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS club_leaders (
                id SERIAL PRIMARY KEY,
                club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
                staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
                appointed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(club_id, staff_id)
            );
        """))
        print("✅ Table created.")
        
        # 2. Migrate existing leaders
        # Copy data from clubs.leader_id -> club_leaders
        await session.execute(text("""
            INSERT INTO club_leaders (club_id, staff_id)
            SELECT id, leader_id FROM clubs 
            WHERE leader_id IS NOT NULL
            ON CONFLICT (club_id, staff_id) DO NOTHING;
        """))
        print("✅ Data migrated.")
        
        # 3. Note: We keep clubs.leader_id for backward compatibility for a bit, or make it nullable and ignored.
        # Ideally we should drop it or stop using it. I'll just stop using it in code.
        
        await session.commit()
        print("🎉 Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
