
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select, update, or_

async def run():
    async with AsyncSessionLocal() as session:
        print("Starting Faculty Normalization...")
        
        # 1. Jurnalistika -> ID 36
        tgt_name = "Jurnalistika fakulteti"
        tgt_id = 36
        print(f"Updating '{tgt_name}' (ID {tgt_id})...")
        stmt = (
            update(Student)
            .where(Student.faculty_name.ilike("%Jurnalistika%"))
            .values(faculty_id=tgt_id, faculty_name=tgt_name)
        )
        await session.execute(stmt)
        
        # 2. PR -> ID 34
        tgt_name = "PR va menejment fakulteti"
        tgt_id = 34
        print(f"Updating '{tgt_name}' (ID {tgt_id})...")
        stmt = (
            update(Student)
            .where(Student.faculty_name.ilike("%PR va menejment%"))
            .values(faculty_id=tgt_id, faculty_name=tgt_name)
        )
        await session.execute(stmt)

        # 3. Xalqaro -> ID 35
        tgt_name = "Xalqaro munosabatlar va ijtimoiy-gumanitar fanlar fakulteti"
        tgt_id = 35
        print(f"Updating '{tgt_name}' (ID {tgt_id})...")
        stmt = (
            update(Student)
            .where(Student.faculty_name.ilike("%Xalqaro munosabatlar%"))
            .values(faculty_id=tgt_id, faculty_name=tgt_name)
        )
        await session.execute(stmt)

        # 4. Magistratura -> ID 37
        tgt_name = "Magistratura bo'limi"
        tgt_id = 37
        print(f"Updating '{tgt_name}' (ID {tgt_id})...")
        stmt = (
            update(Student)
            .where(Student.faculty_name.ilike("%Magistratura%"))
            .values(faculty_id=tgt_id, faculty_name=tgt_name)
        )
        await session.execute(stmt)

        # 5. Sirtqi -> ID 42 (Mapping Sirtqi bo'limi -> SIRTQI FAKULTET canonical ID)
        # Choosing "Sirtqi bo'limi" as the name because it's more readable than SIRTQI FAKULTET (all caps), 
        # BUT checking list_faculties.py, ID 42 matches 'SIRTQI FAKULTET'. 
        # If I change name to 'SIRTQI FAKULTET', it matches the Faculty table.
        # Let's align with Faculty table name for consistency.
        tgt_name = "SIRTQI FAKULTET"
        tgt_id = 42
        print(f"Updating '{tgt_name}' (ID {tgt_id})...")
        stmt = (
            update(Student)
            .where(or_(Student.faculty_name.ilike("%Sirtqi%"), Student.faculty_name.ilike("%SIRTQI%")))
            .values(faculty_id=tgt_id, faculty_name=tgt_name)
        )
        await session.execute(stmt)

        await session.commit()
        print("Normalization Complete.")

if __name__ == "__main__":
    asyncio.run(run())
