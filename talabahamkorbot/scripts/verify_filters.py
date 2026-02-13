
import asyncio
import sys
import os
import aiohttp

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

# Mock Staff for dependencies (or just use direct DB calls if easier, but we want to test endpoints logic if possible)
# Actually, testing endpoints requires running server. Detailed unit test is better.
# But since I can't easily hit localhost:8000 from here without knowing if it's up and accessible (it should be).
# Let's try to verify the logic by importing the router functions directly and passing a mock staff/db.

from api.management import (
    get_mgmt_faculties, 
    get_mgmt_education_types, 
    get_mgmt_levels, 
    get_mgmt_specialties, 
    get_mgmt_groups_list,
    search_mgmt_students
)

async def run():
    async with AsyncSessionLocal() as session:
        print("--- Verifying Filter Logic ---")
        
        # 1. Mock Staff (Admin with University ID)
        stmt = select(Staff).where(Staff.university_id != None).limit(1)
        staff = (await session.execute(stmt)).scalar()
        if not staff:
            print("No staff with university_id found for testing.")
            return

        print(f"Testing as Staff: {staff.full_name} (Role: {staff.role}, Uni ID: {staff.university_id})")
        
        # 2. Get Faculties
        print("\n1. Fetching Faculties...")
        faculties = await get_mgmt_faculties(staff=staff, db=session)
        fac_list = faculties['data']
        print(f"Found {len(fac_list)} faculties.")
        
        if not fac_list:
            print("No faculties, stopping.")
            return

        # Pick "Jurnalistika" or first one
        target_fac = next((f for f in fac_list if "Jurnalistika" in f['name']), fac_list[0])
        fac_id = target_fac['id']
        print(f"Selected Faculty: {target_fac['name']} (ID: {fac_id})")
        
        # 3. Get Types (Dependent on Faculty)
        print(f"\n2. Fetching Types for Faculty ID {fac_id}...")
        types = await get_mgmt_education_types(faculty_id=fac_id, staff=staff, db=session)
        type_list = types['data']
        print(f"Types: {type_list}")
        
        if not type_list:
            print("No types, stopping.")
            return
            
        target_type = type_list[0]
        print(f"Selected Type: {target_type}")

        # 4. Get Levels (Dependent on Faculty + Type)
        print(f"\n3. Fetching Levels for Fac {fac_id} + Type {target_type}...")
        levels = await get_mgmt_levels(faculty_id=fac_id, education_type=target_type, staff=staff, db=session)
        level_list = levels['data']
        print(f"Levels: {level_list}")
        
        if not level_list:
            print("No levels, stopping.")
            return
            
        target_level = level_list[0]
        print(f"Selected Level: {target_level}")

        # 5. Get Specialties (Dependent on Fac + Type + Level)
        print(f"\n4. Fetching Specialties for Fac {fac_id} + Type {target_type} + Level {target_level}...")
        specs = await get_mgmt_specialties(
            faculty_id=fac_id, 
            education_type=target_type, 
            level_name=target_level, 
            staff=staff, 
            db=session
        )
        spec_list = specs['data']
        print(f"Specialties: {len(spec_list)} found. First: {spec_list[0] if spec_list else 'None'}")
        
        target_spec = spec_list[0] if spec_list else None
        
        # 6. Get Groups (Fully Dependent)
        print(f"\n5. Fetching Groups...")
        groups = await get_mgmt_groups_list(
            faculty_id=fac_id,
            education_type=target_type,
            level_name=target_level,
            specialty_name=target_spec,
            staff=staff,
            db=session
        )
        group_list = groups['data']
        print(f"Groups: {len(group_list)} found. First: {group_list[0] if group_list else 'None'}")

        # 7. Search (Final result)
        print(f"\n6. Searching Students...")
        search_res = await search_mgmt_students(
            faculty_id=fac_id,
            education_type=target_type,
            level_name=target_level,
            specialty_name=target_spec,
            staff=staff,
            db=session
        )
        print(f"Search Result: Total {search_res['total_count']}, Data Length: {len(search_res['data'])}")
        
        print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(run())
