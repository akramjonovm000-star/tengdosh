import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import select
from database.db_connect import engine
from database.models import StudentFeedback, Staff, TgAccount

FEEDBACK_ID = 3

async def check_feedback_data():
    async with engine.connect() as conn:
        print(f"--- Checking Feedback ID {FEEDBACK_ID} ---")
        
        # 1. Feedback Info
        result = await conn.execute(select(StudentFeedback).where(StudentFeedback.id == FEEDBACK_ID))
        fb = result.fetchone()
        
        if not fb:
            print("Feedback not found.")
            return

        print(f"Feedback ID: {fb.id}")
        print(f"Status: {fb.status}")
        print(f"Assigned Role: {fb.assigned_role}")
        print(f"Assigned Staff ID: {fb.assigned_staff_id}")

        if not fb.assigned_staff_id:
            print("❌ assigned_staff_id is NULL! Routing will fail.")
            return

        # 2. Staff Info
        staff_res = await conn.execute(select(Staff).where(Staff.id == fb.assigned_staff_id))
        staff = staff_res.fetchone()
        
        if not staff:
            print(f"❌ Staff with ID {fb.assigned_staff_id} NOT found in DB.")
            return

        print(f"Staff Name: {staff.full_name}")
        print(f"Staff Role: {staff.role}")

        # 3. TgAccount Info
        tg_res = await conn.execute(select(TgAccount).where(TgAccount.staff_id == staff.id))
        tg = tg_res.fetchone()

        if not tg:
            print(f"❌ TgAccount for Staff ID {staff.id} NOT found.")
        else:
            print(f"✅ TgAccount found: {tg.telegram_id}")

if __name__ == "__main__":
    asyncio.run(check_feedback_data())
