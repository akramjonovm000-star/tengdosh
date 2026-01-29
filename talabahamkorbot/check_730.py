
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as session:
        st = await session.get(Student, 730)
        if st:
            print(f'ID: {st.id}, Premium: {st.is_premium}, Expiry: {st.premium_expiry}')
        else:
            print('Student 730 not found')

if __name__ == "__main__":
    asyncio.run(check())
