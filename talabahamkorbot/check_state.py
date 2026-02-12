import asyncio
from bot import dp, bot
from aiogram.fsm.storage.base import StorageKey
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student

async def main():
    user_id = 7476703866
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    state = await dp.storage.get_state(key)
    data = await dp.storage.get_data(key)
    print(f"State: {state}")
    print(f"Data: {data}")
    
    async with AsyncSessionLocal() as session:
        tg = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id))
        print(f"TgAccount: {tg}")
        if tg:
            print(f"Student ID: {tg.student_id}")
            if tg.student_id:
                student = await session.get(Student, tg.student_id)
                print(f"Student: {student.full_name if student else 'Not Found'}")

if __name__ == "__main__":
    asyncio.run(main())
