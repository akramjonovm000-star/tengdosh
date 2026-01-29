import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from database.db_connect import AsyncSessionLocal
from database.models import Student, PrivateMessage, UserActivity, StudentSubscription, User

async def main():
    days = 7
    since = datetime.utcnow() - timedelta(days=days)
    print(f"--- Data from the last {days} days (since {since.isoformat()}) ---")
    
    async with AsyncSessionLocal() as session:
        # Students
        stmt = select(func.count(Student.id)).where(Student.created_at >= since)
        r = await session.execute(stmt)
        student_count = r.scalar()
        print(f"\nNew Students: {student_count}")
        
        if student_count > 0:
            stmt = select(Student).where(Student.created_at >= since).order_by(desc(Student.created_at)).limit(5)
            r = await session.execute(stmt)
            students = r.scalars().all()
            for s in students:
                print(f"  - {s.full_name} (HEMIS: {s.hemis_login}) at {s.created_at}")

        # Users (Unified Model)
        stmt = select(func.count(User.id)).where(User.created_at >= since)
        r = await session.execute(stmt)
        user_count = r.scalar()
        print(f"\nNew Users (Unified Table): {user_count}")
        
        if user_count > 0:
            stmt = select(User).where(User.created_at >= since).order_by(desc(User.created_at)).limit(5)
            r = await session.execute(stmt)
            users = r.scalars().all()
            for u in users:
                print(f"  - {u.full_name} (HEMIS: {u.hemis_login}) at {u.created_at}")

        # Messages
        stmt = select(func.count(PrivateMessage.id)).where(PrivateMessage.created_at >= since)
        r = await session.execute(stmt)
        msg_count = r.scalar()
        print(f"\nNew Private Messages: {msg_count}")
        
        if msg_count > 0:
            stmt = select(PrivateMessage).where(PrivateMessage.created_at >= since).order_by(desc(PrivateMessage.created_at)).limit(5)
            r = await session.execute(stmt)
            msgs = r.scalars().all()
            for m in msgs:
                content_preview = m.content[:50] + "..." if len(m.content) > 50 else m.content
                print(f"  - Msg ID {m.id}: {content_preview} at {m.created_at}")

        # User Activities
        stmt = select(func.count(UserActivity.id)).where(UserActivity.created_at >= since)
        r = await session.execute(stmt)
        act_count = r.scalar()
        print(f"\nNew User Activities: {act_count}")

        if act_count > 0:
            stmt = select(UserActivity).where(UserActivity.created_at >= since).order_by(desc(UserActivity.created_at)).limit(5)
            r = await session.execute(stmt)
            acts = r.scalars().all()
            for a in acts:
                print(f"  - {a.name} ({a.category}) at {a.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
