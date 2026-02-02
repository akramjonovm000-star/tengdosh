
import asyncio
import sys
import os
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_connect import AsyncSessionLocal
from database.models import Student, Election

async def debug_visibility():
    login_no_btn = "395251101406"
    login_has_btn = "395251101397"
    
    async with AsyncSessionLocal() as session:
        print("--- DEBUGGING ELECTION VISIBILITY ---")
        
        # 1. Fetch Students
        s1 = await session.scalar(select(Student).where(Student.hemis_login == login_no_btn))
        s2 = await session.scalar(select(Student).where(Student.hemis_login == login_has_btn))
        
        if not s1: print(f"❌ Student {login_no_btn} NOT FOUND")
        else: print(f"👤 Student {login_no_btn} (No Button):\n   Name: {s1.full_name}\n   Uni ID: {s1.university_id}\n   Fac ID: {s1.faculty_id}")
        
        if not s2: print(f"❌ Student {login_has_btn} NOT FOUND")
        else: print(f"👤 Student {login_has_btn} (Has Button):\n   Name: {s2.full_name}\n   Uni ID: {s2.university_id}\n   Fac ID: {s2.faculty_id}")
        
        # 2. Fetch Active Elections
        print("\n--- ACTIVE ELECTIONS ---")
        elections = (await session.execute(select(Election).where(Election.status == 'active'))).scalars().all()
        
        for e in elections:
            print(f"🗳 Election: {e.title}")
            print(f"   ID: {e.id}")
            print(f"   Uni ID: {e.university_id}")
            print(f"   Deadline: {e.deadline}")
            if e.deadline and e.deadline < datetime.utcnow():
                print("   ⚠️ EXPIRED")
            else:
                print("   ✅ ACTIVE")
                
            # Match
            if s1:
                match = (s1.university_id == e.university_id)
                print(f"   Matches Student 1? {match}")
            if s2:
                match = (s2.university_id == e.university_id)
                print(f"   Matches Student 2? {match}")

if __name__ == "__main__":
    asyncio.run(debug_visibility())
