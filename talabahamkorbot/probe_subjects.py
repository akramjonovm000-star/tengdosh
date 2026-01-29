import asyncio
import json
import httpx
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

USER_TG_ID = 8155790902

async def main():
    token = None
    async with AsyncSessionLocal() as session:
        stmt = select(TgAccount).options(joinedload(TgAccount.student)).where(TgAccount.telegram_id == USER_TG_ID)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        if account and account.student:
            token = account.student.hemis_token
    
    if not token:
        print("No token")
        return

    async with httpx.AsyncClient() as client:
        # Check current semester (11)
        resp = await client.get("https://student.jmcu.uz/rest/v1/education/subject-list?semester=11", 
                              headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                print(json.dumps(data[0], indent=2))
            else:
                print("No data found")
        else:
            print(f"Error: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
