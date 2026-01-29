import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import DB_USER, DB_PASS, DB_HOST, DB_NAME, DB_PORT

# Database URL
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def create_club_tables():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # 1. Create 'clubs' table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clubs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                statute_link VARCHAR(500),
                channel_link VARCHAR(500),
                spreadsheet_url VARCHAR(500),
                leader_id INTEGER REFERENCES staff(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        print("✅ 'clubs' table created.")

        # 2. Create 'club_memberships' table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS club_memberships (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                club_id INTEGER REFERENCES clubs(id) ON DELETE CASCADE,
                joined_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(student_id, club_id) 
            );
        """))
        print("✅ 'club_memberships' table created.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_club_tables())
