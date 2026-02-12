import asyncio
import os
import sys
import httpx

# Add parent directory to path
sys.path.append(os.getcwd())

from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Student
from sqlalchemy import select

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

async def probe():
    async with AsyncSessionLocal() as session:
        # Get student 729
        result = await session.execute(select(Student).where(Student.id == 729))
        student = result.scalar_one_or_none()
        
        if not student:
            print("Student 729 not found")
            return

        print(f"Student: {student.full_name}")
        token = student.hemis_token
        # base_url = "https://student.jmcu.uz/rest/v1"
        base_url = "https://student.jmcu.uz/rest/v1"
        
        async with httpx.AsyncClient(verify=False) as client:
            endpoints = [
               ("GET", "/student/document-all"),
               ("GET", "/student/decree"),
               ("GET", "/student/document"),
               ("GET", "/student/reference"),
            ]
            
            for method, ep in endpoints:
                url = f"{base_url}{ep}"
                print(f"\n--- Probing {method} {ep} ---")
                try:
                    response = await client.request(method, url, headers=get_headers(token), timeout=25.0)
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        try:
                             data = response.json()
                             # print(f"Snippet: {str(data)[:500]}")
                             
                             if isinstance(data, dict) and 'data' in data:
                                 items = data['data']
                                 print(f"Count: {len(items)}")
                                 if len(items) > 0:
                                     print(f"Sample Item: {items[0]}")
                             else:
                                 print(f"Data: {str(data)[:200]}")
                        except:
                             print(f"Response Text: {response.text[:200]}")
                    else:
                        print(f"Error: {response.status_code} - {response.text[:200]}")
                except Exception as e:
                    print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(probe())
