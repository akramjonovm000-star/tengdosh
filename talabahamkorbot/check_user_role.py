import asyncio
from database.db_connect import engine
from database.models import Student
from sqlalchemy import select

async def check_role():
    async with engine.connect() as conn:
        print("Checking user 'Javohirxon'...")
        # Search by name loosely or HEMIS ID if we had it exactly
        result = await conn.execute(select(Student.full_name, Student.hemis_id, Student.hemis_role, Student.username)
                                    .where(Student.full_name.ilike("%Javohirxon%")))
        rows = result.fetchall()
        for r in rows:
            print(f"Name: {r.full_name}, Role: {r.hemis_role}, Username: {r.username}")

if __name__ == "__main__":
    asyncio.run(check_role())
