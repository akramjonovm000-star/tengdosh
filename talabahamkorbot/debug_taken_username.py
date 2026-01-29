import asyncio
from database.db_connect import engine
from database.models import TakenUsername, Student
from sqlalchemy import select

async def check():
    async with engine.connect() as conn:
        print("Checking 'javohirxon'...")
        result = await conn.execute(select(TakenUsername.username, TakenUsername.student_id, Student.full_name)
                                    .join(Student, TakenUsername.student_id == Student.id)
                                    .where(TakenUsername.username.ilike("%javoh%")))
        rows = result.fetchall()
        for r in rows:
            print(f"Username: {r.username}, Student ID: {r.student_id}, Name: {r.full_name}")

if __name__ == "__main__":
    asyncio.run(check())
