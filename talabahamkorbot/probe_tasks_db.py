import asyncio
import json
import httpx
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

USER_TG_ID = 8155790902

async def main():
    print("--- Fetching Token from DB ---")
    token = None
    async with AsyncSessionLocal() as session:
        stmt = select(TgAccount).options(joinedload(TgAccount.student)).where(TgAccount.telegram_id == USER_TG_ID)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        if account and account.student:
            token = account.student.hemis_token
            print(f"Token Found: {token[:10]}...")
        else:
            print("User not found or no student linked.")
            return

    print("\n--- Fetching Task List ---")
    async with httpx.AsyncClient() as client:
        url = "https://student.jmcu.uz/rest/v1/data/subject-task-student-list"
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params={"semester": 11, "limit": 200})
        
        if resp.status_code == 200:
             data = resp.json().get("data", [])
             print(f"Found {len(data)} tasks.")
             
             # Group by Subject
             subjects = {}
             for t in data:
                 subj_name = t.get("subject", {}).get("name", "Unknown")
                 grade = t.get("grade", 0) or 0
                 
                 if subj_name not in subjects: subjects[subj_name] = 0
                 subjects[subj_name] += grade
            
             print("\n--- CALCULATED JORIY (TASK SUMS) ---")
             for s, total in subjects.items():
                 print(f"📚 {s}: {total}")
                 
        else:
             print(f"Error: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
