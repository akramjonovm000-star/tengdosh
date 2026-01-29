import asyncio
import logging
import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEMIS_BASE_URL = "https://student.jmcu.uz/rest/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

async def probe():
    async with AsyncSessionLocal() as session:
        tg_id = 8155790902
        stmt = select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student))
        account = await session.scalar(stmt)
        
        if not account or not account.student or not account.student.hemis_token:
            logger.error("Token not found")
            return

        token = account.student.hemis_token
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            # STRICT GUIDE CHECKS
            # 1. Semesters (Optional but checking)
            logger.info("--- Step 1: Semesters ---")
            r = await client.get(f"{HEMIS_BASE_URL}/education/semesters", headers=headers)
            logger.info(f"Semesters: {r.status_code}")
            
            # 2. Subjects with Semester ID
            # Assuming active semester is 11 (or latest from Step 1)
            sem_id = 11 
            logger.info(f"--- Step 2: Subjects (sem={sem_id}) ---")
            r = await client.get(f"{HEMIS_BASE_URL}/education/subjects?semester_id={sem_id}", headers=headers)
            if r.status_code != 200:
                 logger.error(f"Failed subjects: {r.status_code}")
                 # Try subject-list as fallback to get a valid ID if this fails
                 r = await client.get(f"{HEMIS_BASE_URL}/education/subject-list?semester={sem_id}", headers=headers)
            
            data = r.json().get("data", [])
            logger.info(f"Subjects Data Sample: {str(data)[:1000]}")
            if not data:
                logger.error("No subjects found in Step 2")
                return
            
            # Extract ID. Manual says: "subject_id": 77
            # In subject-list, it might be different structure. 
            
            subject_id = None
            subject_name = "Unknown"
            
            s = data[0]
            # Structure observed: [{'subject': {'id': 1067, ...}, ...}]
            if "subject" in s and "id" in s["subject"]:
                 subject_id = s["subject"]["id"]
                 subject_name = s["subject"].get("name")
            elif "subject_id" in s:
                subject_id = s["subject_id"]
                subject_name = s.get("name")
            
            logger.info(f"Testing Subject: {subject_name} (ID: {subject_id})")
            
            # 3. Performance
            # GET /education/performance?subject_id={SUBJECT_ID}
            logger.info("--- Step 3: Performance ---")
            
            # 4. Check subject-list for gradesByExam (My Backup Plan)
            logger.info("--- Step 4: Subject-List Deep Check ---")
            r = await client.get(f"{HEMIS_BASE_URL}/education/subject-list?semester={sem_id}", headers=headers)
            data = r.json().get("data", [])
            if data:
                 sample = data[0]
                 has_grades = "gradesByExam" in sample
                 logger.info(f"Subject-List Sample has gradesByExam? {has_grades}")
                 if has_grades:
                      logger.info(f"GradesByExam Sample: {str(sample['gradesByExam'])[:500]}")
                 else:
                      logger.info(f"Sample Keys: {sample.keys()}")
            else:
                 logger.error("Subject-List Empty")
                 
if __name__ == "__main__":
    asyncio.run(probe())
