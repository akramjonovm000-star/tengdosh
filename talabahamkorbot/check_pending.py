import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import PendingUpload, Student

async def main():
    async with AsyncSessionLocal() as session:
        student_id = 729
        # Check Pending Uploads
        stmt = select(PendingUpload).where(PendingUpload.student_id == student_id)
        result = await session.execute(stmt)
        uploads = result.scalars().all()

        print(f"\n--- Pending Uploads for Student {student_id} ---")
        if not uploads:
            print("No pending uploads found.")
        for up in uploads:
            print(f"Session: {up.session_id} | Files: {up.file_ids} | Created: {up.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
