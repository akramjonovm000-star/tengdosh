import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
import logging
from sqlalchemy import text
from database.db_connect import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    async with engine.begin() as conn:
        try:
            # Check if column exists
            logger.info("Checking for last_active column in tg_accounts...")
            # This is a bit rough for async pg, but we try to just add it and ignore if exists or check information_schema
            # Simpler: just try ADD COLUMN and catch error if needed, or use IF NOT EXISTS if supported (Postgres 9.6+ supports IF NOT EXISTS on ADD COLUMN)
            
            await conn.execute(text("ALTER TABLE tg_accounts ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL;"))
            logger.info("Successfully added 'last_active' column to 'tg_accounts'.")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
