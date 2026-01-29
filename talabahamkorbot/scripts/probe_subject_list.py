import asyncio
import httpx
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

HEMIS_URL = "https://student.jmcu.uz"

async def probe_subjects():
    async with AsyncSessionLocal() as session:
        # Get a student with token
        result = await session.execute(select(Student).where(Student.hemis_token.is_not(None)))
        student = result.scalars().first()
        
        if not student:
            print("❌ No student with token found.")
            return
            
        print(f"👤 Using Student: {student.full_name}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {student.hemis_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            
            url = f"{HEMIS_URL}/rest/v1/education/subject-list"
            print(f"🚀 GET {url}")
            
            resp = await client.get(url, headers=headers)
            print(f"📡 Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", [])
                print(f"📦 Items Found: {len(items)}")
                
                if items:
                    print("🔍 First Item Structure:")
                    print(json.dumps(items[0], indent=2, ensure_ascii=False))
                    
                    # Check subject field specifically
                    subj = items[0].get("subject")
                    print("\n🔍 'subject' field:")
                    print(json.dumps(subj, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(probe_subjects())
