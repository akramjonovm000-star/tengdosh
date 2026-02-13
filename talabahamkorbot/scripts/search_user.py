
import asyncio
from sqlalchemy import select, cast, String
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff, User, TgAccount

async def search(partial_id: str):
    async with AsyncSessionLocal() as session:
        print(f"🔍 Searching for partial ID: {partial_id}")
        
        # Search Students
        res = await session.execute(select(Student.hemis_id, Student.full_name, Student.hemis_login).where(
            (Student.hemis_id.like(f"%{partial_id}%")) | (Student.hemis_login.like(f"%{partial_id}%"))
        ))
        students = res.all()
        print(f"Students found by HEMIS ID/Login: {len(students)}")
        for s in students:
            print(f"  - HEMIS ID: {s.hemis_id}, Login: {s.hemis_login}: {s.full_name}")

        # Search Staff
        res = await session.execute(select(Staff.hemis_id, Staff.jshshir, Staff.full_name).where(
            (cast(Staff.hemis_id, String).like(f"%{partial_id}%")) | (Staff.jshshir.like(f"%{partial_id}%"))
        ))
        staff = res.all()
        print(f"Staff found: {len(staff)}")
        for s in staff:
            print(f"  - HEMIS: {s.hemis_id}, JSHSHIR: {s.jshshir}: {s.full_name}")

        # Search TgAccount
        if partial_id.isdigit():
            res = await session.execute(select(TgAccount.telegram_id, TgAccount.hemis_id).where(
                (TgAccount.telegram_id == int(partial_id)) | (TgAccount.hemis_id.like(f"%{partial_id}%"))
            ))
            accounts = res.all()
            print(f"TgAccounts found: {len(accounts)}")
            for a in accounts:
                print(f"  - TID: {a.telegram_id}, HEMIS: {a.hemis_id}")

        # Search User table
        res = await session.execute(select(User.hemis_id, User.full_name).where(cast(User.hemis_id, String).like(f"%{partial_id}%")))
        users = res.all()
        print(f"Users found by HEMIS ID: {len(users)}")
        for u in users:
            print(f"  - {u.hemis_id}: {u.full_name}")

if __name__ == "__main__":
    import sys
    search_term = sys.argv[1] if len(sys.argv) > 1 else "395251101397"
    asyncio.run(search(search_term))
