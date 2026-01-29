
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from database.models import Base

# Force Test Mode params manually for creation
TEST_DB_NAME = "talabahamkorbot_db_test"

async def setup_test_db():
    print(f"--- SETTING UP TEST ENVIRONMENT: {TEST_DB_NAME} ---")
    
    # 1. Connect to Default DB (postgres) to create new DB
    # We use 'template1' or 'postgres' as maintenance DB
    maintenance_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    
    engine_main = create_async_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    
    async with engine_main.begin() as conn:
        # Check if exists
        exists = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'"))
        if exists.scalar():
            print(f"⚠️ Database '{TEST_DB_NAME}' already exists.")
            # Optional: Drop it? User said "Alohida joy yarat", maybe clean slate is better?
            # Let's NOT drop by default to preserve history if run multiple times, 
            # OR drop if user wants fresh start. 
            # Be safe: Don't drop.
        else:
            print(f"Creating database '{TEST_DB_NAME}'...")
            await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
            print("✅ Database created.")

    await engine_main.dispose()

    # 2. Connect to New Test DB and Migrate
    print("Applying Migrations...")
    test_db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"
    engine_test = create_async_engine(test_db_url)
    
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Schema created (Tables created).")
        
    await engine_test.dispose()
    print("--- SETUP COMPLETE ---")
    print(f"Run backend with: TEST_MODE=true python main.py")

if __name__ == "__main__":
    asyncio.run(setup_test_db())
