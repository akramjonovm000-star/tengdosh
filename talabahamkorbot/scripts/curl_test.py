import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select
from httpx import AsyncClient

async def get_token():
    async with AsyncSessionLocal() as session:
        student = await session.scalar(select(Student).where(Student.hemis_login == "395251101417"))
            
        if student:
            return student.hemis_token
    return None

async def fetch():
    token = await get_token()
    if token:
        print(f"Got token: {token[:10]}...")
        headers = {"Authorization": f"Bearer {token}"}
        
        async with AsyncClient() as client:
            try:
                # We need to test the actual endpoint but it might not be running locally on 8000,
                # so we will use TestClient
                pass
            except Exception as e:
                print("Request failed:", e)

if __name__ == "__main__":
    asyncio.run(fetch())
