import asyncio
from database.db_connect import engine
from database.models import Base, TakenUsername, Student
from sqlalchemy import text, select

async def migrate():
    async with engine.begin() as conn:
        print("Creating taken_usernames table...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("Populating taken_usernames from existing students...")
        # We need to manually select and insert because create_all only creates table structure
        
    async with engine.connect() as conn:
        # Check if we need to migrate existing usernames
        result = await conn.execute(select(Student.id, Student.username).where(Student.username.is_not(None)))
        students = result.fetchall()
        
        for s_id, username in students:
            # Check if exists
            exists = await conn.scalar(select(TakenUsername).where(TakenUsername.username == username))
            if not exists:
                print(f"Migrating {username} for Student {s_id}")
                await conn.execute(
                    text("INSERT INTO taken_usernames (username, student_id, created_at) VALUES (:u, :s, NOW())"),
                    {"u": username, "s": s_id}
                )
        await conn.commit()
    
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
