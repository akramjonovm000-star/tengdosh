import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup, Student

async def main():
    async with AsyncSessionLocal() as db:
        # Check Maxmanazarov
        tutor_id = 74
        groups_result = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor_id))
        group_numbers = groups_result.scalars().all()
        print(f"Groups length: {len(group_numbers)}")
        
        # Test Active count with Student.last_active_at != None
        active_student_count = await db.scalar(
            select(func.count(Student.id))
            .where(
                Student.group_number.in_(group_numbers),
                Student.last_active_at != None
            )
        )
        print(f"Active count (last_active_at): {active_student_count}")
        
        # Test count with User joined
        from database.models import User
        active_student_count2 = await db.scalar(
            select(func.count(Student.id))
            .join(User, User.hemis_login == Student.hemis_login)
            .where(
                Student.group_number.in_(group_numbers)
            )
        )
        print(f"Active count (joined User): {active_student_count2}")

if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())
