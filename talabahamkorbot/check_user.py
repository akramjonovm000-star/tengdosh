import asyncio
import os
from database.db_connect import AsyncSessionLocal
from database.models import Student, User
from sqlalchemy import select

async def check_user_sync():
    async with AsyncSessionLocal() as db:
        # 1. Fetch Student 730
        student = await db.get(Student, 730)
        if not student:
            print("Student 730 NOT FOUND")
            return

        print(f"Student 730: Login='{student.hemis_login}' Name='{student.full_name}'")

        # 2. Fetch User by Login
        if student.hemis_login:
            user = await db.scalar(select(User).where(User.hemis_login == student.hemis_login))
            if user:
                print(f"User FOUND by Login: ID={user.id} Login='{user.hemis_login}'")
            else:
                print(f"User NOT FOUND by Login '{student.hemis_login}'")
        
        # 3. Fetch User by Name
        user_by_name = await db.scalar(select(User).where(User.full_name == student.full_name))
        if user_by_name:
            print(f"User FOUND by Name: ID={user_by_name.id} Login='{user_by_name.hemis_login}'")
        else:
            print(f"User NOT FOUND by Name '{student.full_name}'")

        # 4. List all Users (limit 5)
        users = await db.execute(select(User).limit(5))
        print("Total Users Sample:")
        for u in users.scalars():
             print(f" - {u.id}: {u.hemis_login}")

if __name__ == "__main__":
    asyncio.run(check_user_sync())
