import asyncio
import logging
import json
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount
from services.hemis_service import HemisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ2MVwvYXV0aFwvbG9naW4iLCJhdWQiOiJ2MVwvYXV0aFwvbG9naW4iLCJleHAiOjE3NjkxNjE4OTcsImp0aSI6IjM5NTI1MTEwMTQxMSIsInN1YiI6IjgzMDAifQ.Wxer16yq1E5eSJT7x2aLqTPRWO_TljCIkQsbEJ-2NHg"
USER_TG_ID = 8155790902

async def main():
    print(f"--- Probing Grades for Token ---")
    
    # Try different Semester Params
    variations = [
        ("Code 11", 11),
        ("ID 2023", 2023),
        ("None", None)
    ]
    
    for label, sem in variations:
        print(f"\n--- Testing Semester: {label} ---")
        grades = await HemisService.get_student_subject_list(USER_TOKEN, semester_code=sem)
        
        if grades:
            # Check PR VA REKLAMA
            target = next((i for i in grades if "PR VA REKLAMA" in i.get("curriculumSubject", {}).get("subject", {}).get("name", "")), None)
            if target:
                 print(json.dumps(target.get("gradesByExam", []), indent=2))
            else:
                 print("Subject not found in list.")
        else:
            print("No data.")

if __name__ == "__main__":
    asyncio.run(main())
