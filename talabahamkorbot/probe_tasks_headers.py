import asyncio
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
        else:
            print("User not found")
            return

    url = "https://student.jmcu.uz/rest/v1/data/subject-task-student-list"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://student.jmcu.uz/dashboard/tasks-list",
        "Origin": "https://student.jmcu.uz",
        "X-Requested-With": "XMLHttpRequest"
    }

    print(f"--- Probing {url} with Full Headers ---")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params={"semester": 11, "limit": 200})
        
        if resp.status_code == 200:
             print("✅ SUCCESS!")
             data = resp.json().get("data", [])
             print(f"Found {len(data)} tasks.")
             
             subjects = {}
             for t in data:
                 s_name = t.get("subject", {}).get("name", "Unknown")
                 grade = t.get("grade", 0) or 0
                 if s_name not in subjects: subjects[s_name] = 0
                 subjects[s_name] += grade
            
             print("\n--- CALCULATED JORIY (TASK SUMS) ---")
             for s, total in subjects.items():
                 print(f"📚 {s}: {total}")
        else:
             print(f"❌ Error: {resp.status_code}")
             print(resp.text[:500])

if __name__ == "__main__":
    asyncio.run(main())
