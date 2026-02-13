import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Student).where(Student.full_name == 'MANSUROVA A. N.'))
        row = res.scalar_one_or_none()
        if row:
            print(f'Full Name: {row.full_name}')
            print(f'Short Name: {row.short_name}')
            # Since first_name, last_name, etc. are not model attributes, 
            # we can't check them directly if they aren't in the model.
            # Wait, I checked the model and they ARE NOT there.
        else:
            print('Student not found')

if __name__ == "__main__":
    asyncio.run(run())
