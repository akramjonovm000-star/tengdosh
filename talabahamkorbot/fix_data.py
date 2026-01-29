
import asyncio
from sqlalchemy import select, text
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, Student, University

async def fix_data():
    async with AsyncSessionLocal() as session:
        # 1. Ensure a University Exists
        result = await session.execute(select(University).limit(1))
        uni = result.scalars().first()
        
        if not uni:
            print("Creating Test University...")
            uni = University(
                uni_code="TEST_UNI",
                name="Test University (Toshkent)",
                id=1
            )
            session.add(uni)
            await session.commit()
            print("Created Test University ID: 1")
        else:
            print(f"Using existing University: {uni.name} (ID: {uni.id})")

        # 2. Update Students with NULL university
        print("Updating Students...")
        await session.execute(
            text(f"UPDATE students SET university_id = {uni.id} WHERE university_id IS NULL")
        )
        
        # 3. Update Posts with NULL target_university
        print("Updating Posts...")
        await session.execute(
            text(f"UPDATE choyxona_posts SET target_university_id = {uni.id} WHERE target_university_id IS NULL")
        )
        
        await session.commit()
    print("Data Fixed. All nulls assigned to ID 1.")

if __name__ == "__main__":
    asyncio.run(fix_data())
