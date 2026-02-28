import asyncio
from database.db_connect import engine
from database.models import Staff, TutorGroup
from sqlalchemy import select

async def main():
    async with engine.begin() as conn:
        res = await conn.execute(select(Staff).where(Staff.role == 'tutor').limit(1))
        tutor = res.first()
        if not tutor:
            print("No tutors")
            return
            
        print(f"Tutor Telegram ID: {tutor.telegram_id}")

if __name__ == "__main__":
    asyncio.run(main())
