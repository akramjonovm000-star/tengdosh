
import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def inspect_student_data():
    async with AsyncSessionLocal() as session:
        for sid in [729, 730]:
            print(f"\n--- Student {sid} Data Lengths ---")
            s = await session.get(Student, sid)
            if s:
                for attr in ['full_name', 'group_number', 'faculty_name', 'phone', 'university_name', 'specialty_name', 'semester_name', 'level_name', 'student_status', 'education_form']:
                    val = getattr(s, attr)
                    length = len(val) if val else 0
                    print(f"  {attr}: '{val}' (len={length})")
            else:
                print(f"  ID {sid} not found")

if __name__ == "__main__":
    asyncio.run(inspect_student_data())
