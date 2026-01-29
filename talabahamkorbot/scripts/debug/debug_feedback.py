import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import select
from database.db_connect import engine
from database.models import Staff, TgAccount, StudentFeedback, Student, StaffRole

TG_ID = 2086982893

async def check_feedback():
    async with engine.connect() as conn:
        # 1. Staff Info
        result = await conn.execute(select(Staff).join(TgAccount).where(TgAccount.telegram_id == TG_ID))
        staff = result.fetchone()
        
        if not staff:
            print("Staff not found!")
            return

        print(f"Staff: {staff.full_name}, Role: {staff.role}, FacultyID: {staff.faculty_id}")

        # 2. Check Appeals for this Faculty
        if staff.faculty_id:
            query = select(StudentFeedback.id, StudentFeedback.assigned_role, StudentFeedback.status, Student.faculty_id, Student.full_name)\
                .join(Student)\
                .where(Student.faculty_id == staff.faculty_id)
            
            appeals = await conn.execute(query)
            rows = appeals.fetchall()
            print(f"\n--- Appeals for Faculty {staff.faculty_id} ---")
            for row in rows:
                print(f"ID: {row.id}, Assigned: '{row.assigned_role}', Status: '{row.status}', StudentFac: {row.faculty_id}, Name: {row.full_name}")
        else:
            print("Staff has no faculty_id")

if __name__ == "__main__":
    asyncio.run(check_feedback())
