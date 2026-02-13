import asyncio
import sys
import os
import pandas as pd
from sqlalchemy import select, and_
from sqlalchemy.orm import aliased

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount

# Artifacts directory
ARTIFACT_DIR = "/home/user/.gemini/antigravity/brain/afb35061-766a-4ac4-9df3-85b5ab5f79d8"
OUTPUT_FILE = os.path.join(ARTIFACT_DIR, "pr_va_menejment_non_registered.xlsx")

async def main():
    print("Connecting to database...")
    async with AsyncSessionLocal() as session:
        # Query: Students in Faculty 34 who do NOT have a TgAccount
        # We use a LEFT OUTER JOIN and check for NULL on the right side
        
        stmt = (
            select(Student.full_name, Student.group_number, Student.level_name)
            .outerjoin(TgAccount, Student.id == TgAccount.student_id)
            .where(
                and_(
                    Student.faculty_id == 34,
                    TgAccount.id.is_(None)
                )
            )
            .order_by(Student.group_number, Student.full_name)
        )
        
        result = await session.execute(stmt)
        students = result.all()
        
        print(f"Found {len(students)} non-registered students in faculty 34.")
        
        if not students:
            print("No students found. Exiting.")
            return

        # Convert to DataFrame
        data = [
            {
                "F.I.SH": s.full_name,
                "Guruh": s.group_number,
                "Kurs": s.level_name
            }
            for s in students
        ]
        
        df = pd.DataFrame(data)
        
        # Save to Excel
        print(f"Saving to {OUTPUT_FILE}...")
        df.to_excel(OUTPUT_FILE, index=False)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
