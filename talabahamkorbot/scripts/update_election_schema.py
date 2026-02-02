import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def update_schema():
    async with engine.begin() as conn:
        # Add is_election_admin to students
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN is_election_admin BOOLEAN DEFAULT FALSE"))
            print("Added is_election_admin to students")
        except Exception as e:
            print(f"Students update skipped or failed: {e}")

        # Add status and deadline to elections
        try:
            await conn.execute(text("ALTER TABLE elections ADD COLUMN status VARCHAR(20) DEFAULT 'draft'"))
            await conn.execute(text("ALTER TABLE elections ADD COLUMN deadline TIMESTAMP WITHOUT TIME ZONE"))
            print("Added status and deadline to elections")
        except Exception as e:
            print(f"Elections update skipped or failed: {e}")

        # Add photo_id to election_candidates
        try:
            await conn.execute(text("ALTER TABLE election_candidates ADD COLUMN photo_id VARCHAR(255)"))
            print("Added photo_id to election_candidates")
        except Exception as e:
            print(f"Election candidates update skipped or failed: {e}")

    print("Schema update completed.")

if __name__ == "__main__":
    asyncio.run(update_schema())
