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
            
        token = student.hemis_token

    async with httpx.AsyncClient(verify=False) as client:
        try:
             resp = await client.get("https://student.jmcu.uz/rest/v1/education/subject-list", 
                                   headers={"Authorization": f"Bearer {token}"})
             if resp.status_code == 200:
                 data = resp.json().get("data", [])
                 if data:
                     item = data[0]
                     print("ROOT KEYS:", list(item.keys()))
                     
                     if "curriculumSubject" in item:
                         print("\nCURRICULUM_SUBJECT:", json.dumps(item["curriculumSubject"], indent=2, ensure_ascii=False))
                     
                     if "subject" in item:
                         print("\nSUBJECT:", json.dumps(item["subject"], indent=2, ensure_ascii=False))
                 else:
                     print("No data found")
             else:
                 print(f"Error: {resp.status_code}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
