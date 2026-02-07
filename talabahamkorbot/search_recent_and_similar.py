import asyncio
from sqlalchemy import select, or_
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity, TgAccount

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Search for students with "Muxammad" or "Akram"
        print("--- Searching for students with 'Muxammad' or 'Akram' ---")
        stmt = select(Student).where(
            (Student.full_name.ilike("%Muxammad%")) | 
            (Student.full_name.ilike("%Akram%"))
        )
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        for s in students:
            # Count activities
            stmt_act = select(UserActivity).where(UserActivity.student_id == s.id)
            res_act = await session.execute(stmt_act)
            acts = res_act.scalars().all()
            
            if len(acts) > 0:
                print(f"FOUND: {s.full_name} | ID: {s.id} | Activities: {len(acts)}")
            
        # 2. Check for activities in the last 7 days
        print("\n--- Activities in the last 7 days ---")
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        stmt = select(UserActivity).where(UserActivity.created_at >= seven_days_ago)
        result = await session.execute(stmt)
        acts = result.scalars().all()
        print(f"Total recent activities: {len(acts)}")
        for a in acts:
            s = await session.get(Student, a.student_id)
            s_name = s.full_name if s else "Unknown"
            print(f"[{a.id}] {s_name} (ID: {a.student_id}) | Name: {a.name} | Status: {a.status} | Created: {a.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
