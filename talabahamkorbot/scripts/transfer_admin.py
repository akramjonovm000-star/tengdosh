import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student

async def transfer_rights():
    async with AsyncSessionLocal() as session:
        # 1. Revoke from 395251101397
        stmt1 = select(Student).where(Student.hemis_login == "395251101397")
        student1 = await session.scalar(stmt1)
        if student1:
            student1.is_election_admin = False
            print("Revoked from 395251101397 (ID: {})".format(student1.full_name))
        else:
            print("HEMIS 395251101397 not found")

        # 2. Grant to 395251101411
        stmt2 = select(Student).where(Student.hemis_login == "395251101411")
        student2 = await session.scalar(stmt2)
        if student2:
            student2.is_election_admin = True
            print("Granted to 395251101411 (ID: {})".format(student2.full_name))
        else:
            print("HEMIS 395251101411 not found")
        
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(transfer_rights())
