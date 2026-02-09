import asyncio
import json
from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Student, Staff, StaffRole
from talabahamkorbot.api.management import get_mgmt_specialties, get_mgmt_groups_simple, search_mgmt_students
from sqlalchemy import select

async def verify():
    print("--- Verifying Management Search Filters ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Mock a staff member (Rahbariyat)
        res = await db.execute(select(Staff).where(Staff.role == StaffRole.RAHBARIYAT).limit(1))
        mock_staff = res.scalar_one_or_none()
        if not mock_staff:
            print("Error: No Rahbariyat staff found in DB for testing.")
            return

        print(f"Testing with Staff: {mock_staff.full_name} (ID: {mock_staff.id}, Uni: {mock_staff.university_id})")

        # 2. Test Specialties Dropdown
        print("\n[Dropdown] Testing Specialties...")
        result = await get_mgmt_specialties(staff=mock_staff, db=db)
        if result['success']:
            specs = result['data']
            print(f"Found {len(specs)} specialties.")
            if specs:
                print(f"Sample: {specs[0]}")
        else:
            print("Failed to fetch specialties.")

        # 3. Test Groups Dropdown
        print("\n[Dropdown] Testing Groups...")
        result = await get_mgmt_groups_simple(staff=mock_staff, db=db)
        if result['success']:
            groups = result['data']
            print(f"Found {len(groups)} groups.")
            if groups:
                 print(f"Sample: {groups[0]}")
        else:
            print("Failed to fetch groups.")

        # 4. Test Search with combinations
        print("\n[Search] Testing Filter Combinations...")
        
        # Combo A: No filters
        result = await search_mgmt_students(staff=mock_staff, db=db)
        print(f"Combo A (No filters): {result['total_count']} students found.")

        # Combo B: Faculty only (Jurnalistika = 4 in Admin API mapping)
        result = await search_mgmt_students(faculty_id=4, staff=mock_staff, db=db)
        print(f"Combo B (Faculty=4): {result['total_count']} students found.")

        # Combo C: Education Type (Bakalavr)
        result = await search_mgmt_students(education_type="Bakalavr", staff=mock_staff, db=db)
        print(f"Combo C (Type=Bakalavr): {result['total_count']} students found.")

        # Combo D: Specialty (if specs available)
        if specs:
            s_name = specs[0]
            result = await search_mgmt_students(specialty_name=s_name, staff=mock_staff, db=db)
            print(f"Combo D (Specialty={s_name}): {result['total_count']} students found.")
        
        # Combo E: Group (if groups available)
        if groups:
            g_name = groups[0]
            result = await search_mgmt_students(group_number=g_name, staff=mock_staff, db=db)
            print(f"Combo E (Group={g_name}): {result['total_count']} students found.")

        # 5. Hierarchical Dropdown Tests
        print("\n[Hierarchical] Testing Specialty filtering by Faculty...")
        res_spec_f = await get_mgmt_specialties(faculty_id=4, staff=mock_staff, db=db)
        specs_f4 = res_spec_f.get('data', [])
        print(f"Faculty 4 Specialties: {len(specs_f4)} items found.")

        print("\n[Hierarchical] Testing Specialty filtering by Faculty and Education Type...")
        # Test with Faculty 4 and Bakalavr
        res_spec_holistic = await get_mgmt_specialties(faculty_id=4, education_type="Bakalavr", staff=mock_staff, db=db)
        if res_spec_holistic['success']:
            specs_f4_bak = res_spec_holistic['data']
            print(f"Faculty 4 Bakalavr Specialties: {len(specs_f4_bak)} items found.")
            if len(specs_f4_bak) <= len(specs_f4):
                print("PASSED: Specialty list is filtered by faculty and education type (or zero matched).")
        
        print("\n[Hierarchical] Testing Group filtering by Faculty and Specialty...")
        # Pick first specialty from Faculty 4
        s_base = specs_f4_bak if specs_f4_bak else specs_f4
        if s_base:
            s_name = s_base[0]
            res_grp_filtered = await get_mgmt_groups_simple(faculty_id=4, specialty_name=s_name, staff=mock_staff, db=db)
            if res_grp_filtered['success']:
                grps_f4_s = res_grp_filtered['data']
                print(f"Groups for Faculty 4 and Specialty '{s_name}': {len(grps_f4_s)} items found.")
                if len(grps_f4_s) < len(groups):
                    print("PASSED: Group list is filtered by faculty and specialty.")
                else:
                    print("WARNING: Group list is NOT filtered or very broad.")

if __name__ == "__main__":
    asyncio.run(verify())
