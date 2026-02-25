import asyncio
import sys
import logging
from database.db_connect import engine, Base
from database.models import YetakchiActivity, YetakchiEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_new_tables():
    logger.info("Connecting to database specifically for Yetakchi module tables...")
    async with engine.begin() as conn:
        logger.info("Creating new tables if they don't exist...")
        
        # We manually specify tables to avoid running create_all for entire DB which might have issues
        # Actually create_all with checkfirst=True is safe
        await conn.run_sync(Base.metadata.create_all, tables=[
            YetakchiActivity.__table__,
            YetakchiEvent.__table__
        ], checkfirst=True)
        
        logger.info("Yetakchi tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_new_tables())
