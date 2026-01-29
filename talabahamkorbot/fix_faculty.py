

import asyncio
from sqlalchemy import select, text
from database.db_connect import AsyncSessionLocal
from database.models import Student, Faculty, University

async def fix_faculty():
    async with AsyncSessionLocal() as session:
        # 1. Get/Confirm University
        result = await session.execute(select(University).limit(1))
        uni = result.scalars().first()
        if not uni:
            uni = University(uni_code="TEST_UNI", name="Test University", id=1)
            session.add(uni)
            await session.commit()
        print(f"University: {uni.name}")

        # 2. Sync Faculties from Student Data
        # Find all unique faculty names in Student table
        result_names = await session.execute(select(Student.faculty_name).distinct())
        fac_names = [n for n in result_names.scalars().all() if n]
        
        print(f"Found Faculty Names in Students: {fac_names}")
        
        for f_name in fac_names:
            # Check if Faculty exists
            existing_fac = await session.execute(select(Faculty).where(Faculty.name == f_name))
            fac = existing_fac.scalars().first()
            
            if not fac:
                print(f"Creating missing faculty: {f_name}")
                fac = Faculty(
                    university_id=uni.id,
                    faculty_code=f"AUTO_{f_name.replace(' ', '_')[:20]}",
                    name=f_name,
                    is_active=True
                )
                session.add(fac)
                await session.commit()
                print(f"Created Faculty ID: {fac.id}")
            else:
                 print(f"Faculty already exists: {fac.name} (ID: {fac.id})")
            
            # 3. Update Students belonging to this faculty
            print(f"Updating students for {f_name} (ID: {fac.id})...")
            await session.execute(
                text(f"UPDATE students SET faculty_id = {fac.id} WHERE faculty_name = :f_name"),
                {"f_name": f_name}
            )
            
        # 4. Fallback cleanup (optional)
        await session.commit()
    print("Smart Faculty Sync Complete.")

if __name__ == "__main__":
    asyncio.run(fix_faculty())

