import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # Check available fields for a student in this specialty
        query = select(Student).where(Student.specialty_name.ilike("%Axborot xizmati%")).limit(1)
        result = await db.execute(query)
        s = result.scalar_one_or_none()
        if s:
            from sqlalchemy import inspect
            inst = inspect(s)
            print("Fields:", [c.key for c in inst.mapper.column_attrs])
            # Check likely candidates for grant/contract
            print(f"payment_type: {getattr(s, 'payment_type', 'N/A')}")
            print(f"payment_form: {getattr(s, 'payment_form', 'N/A')}")
            print(f"Contract info: {getattr(s, 'contract_type', 'N/A')}")

asyncio.run(main())
