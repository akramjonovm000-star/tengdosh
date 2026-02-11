import asyncio
from sqlalchemy import select, update, or_
from database.db_connect import AsyncSessionLocal
from database.models import Staff, Student

async def revoke_tutor_tokens():
    async with AsyncSessionLocal() as db:
        print("Starting Token Revocation for Tutors...")
        
        # 1. Clear Tokens for Staff with role 'tyutor' (EXCEPT ID 64 - Nazokat)
        stmt_staff = update(Staff).where(
            Staff.role == 'tyutor',
            Staff.id != 64 
        ).values(hemis_token=None)
        
        result_staff = await db.execute(stmt_staff)
        print(f"Revoked Staff Tokens: {result_staff.rowcount}")
        
        # 2. Clear Tokens for Students with role 'tyutor' (if any exist from earlier bugs)
        stmt_student = update(Student).where(
            or_(Student.hemis_role == 'tyutor')
        ).values(hemis_token=None)
        
        result_student = await db.execute(stmt_student)
        print(f"Revoked Student/Tyutor Tokens: {result_student.rowcount}")
        
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(revoke_tutor_tokens())
