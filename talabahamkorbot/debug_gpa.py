import asyncio
import logging
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache, Student
from sqlalchemy import select
from services.gpa_calculator import GPACalculator
from services.hemis_service import HemisService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_gpa():
    async with AsyncSessionLocal() as session:
        # Get first active student with token
        result = await session.execute(select(Student).where(Student.hemis_token.isnot(None)))
        student = result.scalars().first()
        
        if not student:
            print("No student found with token")
            return

        print(f"Debugging GPA for Student: {student.full_name} (ID: {student.id})")
        token = student.hemis_token
        
        # 1. Get Subjects (likely from Cache if exists)
        # We try to get "Current" semester or just cache
        # Let's peek at StudentCache
        cache_res = await session.execute(select(StudentCache).where(StudentCache.student_id == student.id))
        caches = cache_res.scalars().all()
        
        found_subjects = None
        for c in caches:
            if c.key.startswith("subjects_"):
                print(f"Found Cache Key: {c.key}, updated: {c.updated_at}")
                found_subjects = c.data
                break
        
        if not found_subjects:
            print("No cached subjects found. Fetching live...")
            found_subjects = await HemisService.get_student_subject_list(token)
            
        if not found_subjects:
            print("Could not fetch subjects.")
            return

        print(f"\n--- Analyzing {len(found_subjects)} Subjects ---")
        
        # 2. Run Calculator Logic manually and print details
        total_cr = 0
        total_pts = 0
        old_sum = 0
        old_count = 0
        
        for item in found_subjects:
            # Extraction Logic Copied from GPACalculator
            subject_info = item.get("curriculumSubject", {}) or item.get("subject", {}) or {}
            subj_name = subject_info.get("name") or subject_info.get("subject", {}).get("name") or "Nomsiz"
            
            # CREDIT
            raw_credit = item.get("credit")
            curr_credit = subject_info.get("credit")
            
            try:
                credit = float(raw_credit or curr_credit or 0)
            except: credit = 0.0
            
            # GRADE
            overall = item.get("overallScore")
            final_score = 0.0
            if isinstance(overall, dict):
                final_score = float(overall.get("grade") or 0)
            
            mapped_grade, mapped_point = GPACalculator._map_grade(final_score)
            
            print(f"Subject: {subj_name}")
            print(f"  - Raw Credit keys: item.credit={raw_credit}, currSub.credit={curr_credit}")
            print(f"  - Extracted Credit: {credit}")
            print(f"  - Score: {final_score} -> {mapped_grade} ({mapped_point})")
            
            if credit > 0 and final_score > 0:
                calc_point = mapped_point * credit
                print(f"  - Weighted Point: {calc_point}")
                total_cr += credit
                total_pts += calc_point
            else:
                print("  - EXCLUDED (No credit or score)")
                
            # Old Logic (Simple Average)
            if final_score > 0:
                old_sum += final_score
                old_count += 1
                
        print("\n--- RESULTS ---")
        if total_cr > 0:
            new_gpa = round(total_pts / total_cr, 2)
            print(f"NEW (Weighted 4.0 Scale): {new_gpa} (Total Credits: {total_cr})")
        else:
            print("NEW: 0.0")
            
        if old_count > 0:
            old_gpa = round(old_sum / old_count, 2)
            print(f"OLD (Simple Average 100 Scale): {old_gpa}")
        else:
            print("OLD: 0.0")

if __name__ == "__main__":
    asyncio.run(debug_gpa())
