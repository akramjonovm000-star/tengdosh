import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student
from api.security import create_access_token
from main import app
from fastapi.testclient import TestClient

import asyncio

async def get_token():
    async with AsyncSessionLocal() as db:
        student = await db.scalar(select(Student).where(Student.hemis_login == "395251101397"))
        
        token = create_access_token(
            data={"sub": str(student.id), "id": student.id, "type": "student", "hemis_token": None},
            user_agent="unknown"
        )
        return token

token = asyncio.run(get_token())

client = TestClient(app)
resp = client.get(
    "/api/v1/student/clubs/9/members",
    headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "unknown"
    }
)
print(f"Status: {resp.status_code}")
print(resp.json())
