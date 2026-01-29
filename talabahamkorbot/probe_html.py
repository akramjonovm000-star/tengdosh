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

    # User screenshot shows: student.jmcu.uz/education/performance
    # Network request: performance?semester=11&...
    # This is a WEB route, not REST.
    url = "https://student.jmcu.uz/education/performance"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    }

    print(f"--- Probing {url} (HTML Mode) ---")
    async with httpx.AsyncClient() as client:
        # Try asking for semester 11
        resp = await client.get(url, headers=headers, params={"semester": 11})
        
        if resp.status_code == 200:
             print("✅ SUCCESS!")
             print(f"Content-Type: {resp.headers.get('content-type')}")
             html = resp.text
             print(f"Length: {len(html)}")
             
             if "4.0" in html:
                 print("🎉 FOUND '4.0' in HTML!")
                 
             if "<th" in html and "JN" in html:
                 print("🎉 FOUND Table with JN header!")
                 
             # Dump partial HTML
             print(html[:1000])
        else:
             print(f"❌ Error: {resp.status_code}")
             # Probably 302 Redirect to Login or 401
             print(resp.headers)

if __name__ == "__main__":
    asyncio.run(main())
