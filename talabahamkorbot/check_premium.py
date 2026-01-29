
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_user_premium():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student).where(Student.username == 'joxajon'))
        user = result.scalar_one_or_none()
        if user:
            print(f"User: {user.full_name} (@{user.username})")
            print(f"Is Premium: {user.is_premium}")
            print(f"Trial Used: {user.trial_used}")
        else:
            print("User joxajon not found")

if __name__ == "__main__":
    asyncio.run(check_user_premium())
