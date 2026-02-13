
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff, StudentFeedback, Student
from sqlalchemy import select, update

from api.management_appeals import get_appeals_list

async def run():
    async with AsyncSessionLocal() as session:
        print("--- Verifying Appeals Filters ---")
        
        # 1. Mock Staff (Owner/Admin)
        stmt = select(Staff).where(Staff.role == 'owner', Staff.university_id != None).limit(1)
        staff = (await session.execute(stmt)).scalar()
        if not staff:
            # Fallback
            stmt = select(Staff).where(Staff.role.in_(['rahbariyat', 'rektor']), Staff.university_id != None).limit(1)
            staff = (await session.execute(stmt)).scalar()
            
        if not staff:
            print("No suitable admin staff found.")
            return

        print(f"User: {staff.full_name}")

        # 2. Setup Test Data (Ensure there is at least one appeal with known Faculty and Topic)
        # Find an appeal
        stmt = select(StudentFeedback).join(Student).limit(1)
        appeal = (await session.execute(stmt)).scalar()
        
        if not appeal:
            print("No appeals found to test filters.")
            return
            
        # Update it to have a specific topic for testing
        test_topic = "Davomat_Test"
        await session.execute(
            update(StudentFeedback).where(StudentFeedback.id == appeal.id).values(ai_topic=test_topic)
        )
        await session.commit()
        
        # Get its faculty
        appeal_student = (await session.execute(select(Student).where(Student.id == appeal.student_id))).scalar()
        test_fac_id = appeal_student.faculty_id
        
        if not test_fac_id:
            print("Test appeal has no faculty ID.")
            return
            
        print(f"Test Appeal ID: {appeal.id}, FacID: {test_fac_id}, Topic: {test_topic}")
        
        # 3. Test Faculty Filter
        print("\nTesting Faculty Filter:")
        res_fac = await get_appeals_list(
            faculty_id=test_fac_id,
            staff=staff,
            db=session
        )
        print(f"Found {len(res_fac)} appeals for Faculty {test_fac_id}")
        
        has_test_appeal = any(a['id'] == appeal.id for a in res_fac)
        print(f"Contains Test Appeal? {has_test_appeal}")
        
        # 4. Test Topic Filter
        print("\nTesting Topic Filter:")
        res_topic = await get_appeals_list(
            faculty_id=test_fac_id,
            ai_topic=test_topic,
            staff=staff,
            db=session
        )
        print(f"Found {len(res_topic)} appeals for Topic '{test_topic}'")
        
        has_test_topic = any(a['id'] == appeal.id for a in res_topic)
        print(f"Contains Test Appeal? {has_test_topic}")
        
        if has_test_appeal and has_test_topic:
            print("\nSUCCESS: Filters working correctly.")
        else:
            print("\nFAILURE: Filters not working as expected.")

if __name__ == "__main__":
    asyncio.run(run())
