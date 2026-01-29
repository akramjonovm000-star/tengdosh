import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import select, func
from database.models import TgAccount, Student, ClubMembership
from database.db_connect import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        # Check All Students
        stmt_all = select(func.count(TgAccount.id)).where(TgAccount.student_id.isnot(None))
        count_all = await session.scalar(stmt_all)
        print(f"Total Students (TgAccount with student_id): {count_all}")
        
        # Check Club Members (Total distinct)
        stmt_club = (
            select(func.count(func.distinct(TgAccount.id)))
            .join(Student, TgAccount.student_id == Student.id)
            .join(ClubMembership, Student.id == ClubMembership.student_id)
        )
        count_club = await session.scalar(stmt_club)
        print(f"Total Club Members (Distinct TgAccount): {count_club}")

        # Check raw ClubMemberships
        stmt_raw_cm = select(func.count(ClubMembership.id))
        count_raw = await session.scalar(stmt_raw_cm)
        print(f"Total Raw ClubMembership records: {count_raw}")

if __name__ == "__main__":
    asyncio.run(main())
