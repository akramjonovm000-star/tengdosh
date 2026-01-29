import asyncio
import json
import httpx
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        # Get any student with token
        stmt = select(Student).where(Student.hemis_token.is_not(None)).limit(1)
        result = await session.execute(stmt)
        student = result.scalar_one_or_none()
        
        if not student:
            print("No student with token found")
            return
            
        print(f"Probing Student: {student.full_name}")
        token = student.hemis_token

    async with httpx.AsyncClient(verify=False) as client:
        # Check current semester (try without semester param for default)
        try:
             resp = await client.get("https://student.jmcu.uz/rest/v1/education/subject-list", 
                                   headers={"Authorization": f"Bearer {token}"})
             if resp.status_code == 200:
                 data = resp.json().get("data", [])
                 if data:
                     # Dump first item
                     print(json.dumps(data[0], indent=2, ensure_ascii=False))
                     
                     # Check Key
                     name = data[0].get("subject", {}).get("name")
                     print(f"\nExtracted Name (old method): {name}")
                     
                     keys = data[0].keys()
                     print(f"Available Keys: {list(keys)}")
                     
                     if "subject" in data[0]:
                         print(f"Subject Keys: {data[0]['subject'].keys()}")
                 else:
                     print("No data found")
             else:
                 print(f"Error: {resp.status_code}")
                 print(resp.text)
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
