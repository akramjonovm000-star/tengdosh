import asyncio
import httpx
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

USER_TG_ID = 8155790902
SUBJECT_ID = 1049 

async def main():
    token = None
    async with AsyncSessionLocal() as session:
        stmt = select(TgAccount).options(joinedload(TgAccount.student)).where(TgAccount.telegram_id == USER_TG_ID)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        token = account.student.hemis_token
    
    base_url = "https://student.jmcu.uz/rest/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        print(f"\n--- RESOURCES for Subject {SUBJECT_ID} (Attempt 2) ---")
        try:
            # Attempt 2: Plural 
            url = f"{base_url}/education/resources"
            print(f"Trying: {url} with subject={SUBJECT_ID}")
            r = await client.get(url, headers=headers, params={"subject": SUBJECT_ID, "semester": 11, "page": 1, "limit": 20})
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                import json
                print(json.dumps(r.json(), indent=2))
        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())
