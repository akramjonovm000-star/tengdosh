import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def patch_user():
    async with AsyncSessionLocal() as session:
        # User ID from previous debug output: 728
        s = await session.get(Student, 728)
        if s:
            print(f"Patching student {s.id}...")
            s.university_name = "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti"
            s.faculty_name = "PR va menejment fakulteti"
            await session.commit()
            print("✅ Patched successfully.")
        else:
            print("Student not found.")

if __name__ == "__main__":
    asyncio.run(patch_user())
