import asyncio
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

    base_url = "https://student.jmcu.uz/rest/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Subject List (for Grades)
        print("\n--- SUBJECT LIST (First Item) ---")
        try:
            r = await client.get(f"{base_url}/education/subject-list?semester=11", headers=headers)
            data = r.json().get("data", [])
            if data:
                import json
                # Print first item completely to see gradesByExam
                print(json.dumps(data[0], indent=2))
        except Exception as e:
            print(e)
            
        # 2. Schedule (for Teachers)
        print("\n--- SCHEDULE (Week) ---")
        try:
            # Need date range? Or just /education/schedule default (current week)
            r = await client.get(f"{base_url}/education/schedule", headers=headers)
            data = r.json().get("data", [])
            if data:
                # Print first item to see 'employee' and 'subject' relation
                print(json.dumps(data[0], indent=2))
        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())
