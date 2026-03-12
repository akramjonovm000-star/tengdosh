import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        st = await session.get(Student, 730)
        print(f'Student: {st.full_name}')
        print(f'FCM token: {st.fcm_token}')
        tg = await session.scalar(select(TgAccount).where(TgAccount.student_id == 730))
        if tg:
            print(f'TG Account ID: {tg.telegram_id}')
        else:
            print('No TG Account')

if __name__ == "__main__":
    asyncio.run(main())
