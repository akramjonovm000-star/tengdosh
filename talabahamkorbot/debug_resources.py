import asyncio
import logging
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student
from services.hemis_service import HemisService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_resources():
    async with AsyncSessionLocal() as session:
        # Get first student with token
        result = await session.execute(select(Student).where(Student.hemis_token.isnot(None)))
        student = result.scalars().first()
        
        if not student:
            print("No student found with token.")
            return

        print(f"Testing with Student: {student.full_name} (ID: {student.id})")
        token = student.hemis_token
        
        # 1. Get Subjects
        print("Fetching subjects...")
        subjects = await HemisService.get_student_subject_list(token)
        if not subjects:
            print("No subjects found.")
            return

        print(f"Found {len(subjects)} subjects.")
        
        # 2. Get Current Semester
        print("Fetching ME...")
        me = await HemisService.get_me(token)
        curr_sem = me.get("semester", {}).get("code")
        print(f"Current Semester: {curr_sem}")

        # Loop all subjects
        for subj in subjects:
             curr = subj.get("curriculumSubject", {})
             subj_details = curr.get("subject", {})
             s_id = subj_details.get("id")
             s_name = subj_details.get("name")
             
             # Try to find semester in subject payload
             # Inspecting structure
             subj_sem = subj.get("semester", {}).get("code")
             
             print(f"--- Checking {s_name} (ID: {s_id}) SemInJSON: {subj_sem} ---")
             
             # Try current semester AND detected semester
             sems_to_try = {str(curr_sem)}
             if subj_sem: sems_to_try.add(str(subj_sem))
             
             found = False
             for sm in sems_to_try:
                 res = await HemisService.get_student_resources(token, str(s_id), sm)
                 if res:
                     print(f"✅ FOUND {len(res)} resources with Sem {sm}!")
                     found = True
                     break
             
             if not found:
                 print("❌ No resources found.")

if __name__ == "__main__":
    asyncio.run(test_resources())
