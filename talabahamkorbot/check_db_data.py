
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import UserDocument, UserCertificate, StudentFeedback
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as s:
        d = await s.scalar(select(func.count(UserDocument.id)))
        c = await s.scalar(select(func.count(UserCertificate.id)))
        f = await s.scalar(select(func.count(StudentFeedback.id)))
        print(f"Docs: {d}, Certs: {c}, Feedbacks: {f}")

if __name__ == "__main__":
    asyncio.run(check())
