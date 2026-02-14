import asyncio
import re
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup, Student, Faculty, University, StaffRole, StudentStatus
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REPORT_FILE = "jmcu_analytics_report.md"

async def main():
    if not HEMIS_ADMIN_TOKEN:
        logger.error("HEMIS_ADMIN_TOKEN is missing in config!")
        return

    logger.info("Starting Tutor-Student Synchronization...")
    
    # 1. Parse Report
    data = parse_report(REPORT_FILE)
    logger.info(f"Parsed {len(data)} tutor-group assignments.")
    
    async with AsyncSessionLocal() as session:
        # 2. Process each assignment
        for entry in data:
            faculty_name = entry['faculty']
            group_name = entry['group']
            tutor_name = entry['tutor']
            
            # A. Sync Tutor (Staff)
            if tutor_name not in ['-', '...'] and len(tutor_name) >= 5:
                tutor = await sync_tutor(session, tutor_name, faculty_name)
                
                # B. Sync Group Link
                if tutor:
                    await sync_tutor_group(session, tutor, group_name, faculty_name)
            
            # C. Fetch and Sync Students for this Group (Always, regardless of tutor)
            expected_count = entry.get('expected_count', 0)
            await sync_students(session, group_name, expected_count)

        await session.commit()
    
    logger.info("Synchronization Complete!")

def parse_report(file_path):
    """
    Parses the markdown report to extract:
    [
        {"faculty": "...", "group": "...", "tutor": "..."}
    ]
    """
    results = []
    current_faculty = None
    
    # Regex patterns
    faculty_pat = re.compile(r"^## 🏫 (.*)")
    row_pat = re.compile(r"^\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*(\d+)\s*\|.*")
    
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                
                # Check Faculty Header
                fm = faculty_pat.match(line)
                if fm:
                    current_faculty = fm.group(1).strip()
                    continue
                
                # Check Table Row
                rm = row_pat.match(line)
                if rm and current_faculty:
                    group_raw = rm.group(1).strip()
                    tutor_raw = rm.group(2).strip()
                    count_raw = rm.group(3).strip()
                    
                    # Clean group name (remove sequence, extra info if needed)
                    if "---" in line or "Guruh" in line:
                        continue
                        
                    results.append({
                        "faculty": current_faculty,
                        "group": group_raw,
                        "tutor": tutor_raw,
                        "expected_count": int(count_raw)
                    })
    except FileNotFoundError:
        logger.error(f"Report file {file_path} not found.")
        
    return results

async def sync_tutor(session, full_name, faculty_name):
    # Normalize name for search
    stmt = select(Staff).where(Staff.full_name.ilike(f"%{full_name}%"))
    result = await session.execute(stmt)
    tutors = result.scalars().all()
    
    if len(tutors) > 1:
        logger.warning(f"Multiple staff found for {full_name}. Using the first one (ID: {tutors[0].id}).")
        tutor = tutors[0]
    elif tutors:
        tutor = tutors[0]
    else:
        tutor = None
    
    if not tutor:
        logger.info(f"Creating new Tutor: {full_name}")
        # Identify Faculty ID if possible (simple lookup)
        fac_stmt = select(Faculty).where(Faculty.name.ilike(f"%{faculty_name}%"))
        fac_res = await session.execute(fac_stmt)
        faculty = fac_res.scalar_one_or_none()
        
        tutor = Staff(
            full_name=full_name,
            role=StaffRole.TYUTOR,
            university_id=1, # Default JMCU
            faculty_id=faculty.id if faculty else None,
            is_active=True
        )
        session.add(tutor)
        await session.flush() # Get ID
    
    return tutor

async def sync_tutor_group(session, tutor, group_name, faculty_name):
    # Check if link exists
    stmt = select(TutorGroup).where(
        TutorGroup.tutor_id == tutor.id, 
        TutorGroup.group_number == group_name
    )
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    
    if not link:
        logger.info(f"Linking Group {group_name} to {tutor.full_name}")
        
        # Get Faculty ID
        fac_stmt = select(Faculty).where(Faculty.name.ilike(f"%{faculty_name}%"))
        fac_res = await session.execute(fac_stmt)
        faculty = fac_res.scalar_one_or_none()

        link = TutorGroup(
            tutor_id=tutor.id,
            group_number=group_name,
            university_id=1,
            faculty_id=faculty.id if faculty else None
        )
        session.add(link)
        # Don't need flush usually unless used immediately
        
async def sync_students(session, group_name, expected_count=0):
    # Check if we already have students for this group
    # This allows resuming the script without re-fetching everything
    count_stmt = select(func.count(Student.id)).where(Student.group_number == group_name)
    existing_count = await session.scalar(count_stmt)
    
    # Only skip if we have AT LEAST the expected number of students
    if existing_count > 0 and existing_count >= expected_count:
        logger.info(f"Skipping {group_name}: Has {existing_count}/{expected_count} students.")
        return

    logger.info(f"Fetching students for group: {group_name} (Expected: {expected_count}, Found: {existing_count})")
    
    # Use HemisService to fetch students
    students, count = await HemisService.get_students_for_groups([group_name], HEMIS_ADMIN_TOKEN)
    
    if not students:
        logger.warning(f"No students found for group {group_name} in HEMIS.")
        return

    logger.info(f"Found {len(students)} students. Updating DB...")
    
    for s_data in students:
        hemis_id = str(s_data.get("id"))
        student_id_str = s_data.get("student_id_number") # JSHSHIR or Student ID
        
        # Determine Login (usually student_id_number or hemis_id)
        # Login is critical for uniqueness
        login = student_id_str if student_id_str else hemis_id
        
        # Prepare Data
        # Use format_uzbek_name instead of .title()
        from utils.text_utils import format_uzbek_name
        
        first_name = format_uzbek_name((s_data.get('first_name') or "").strip())
        last_name = format_uzbek_name((s_data.get('second_name') or "").strip())
        patronymic = format_uzbek_name((s_data.get('third_name') or "").strip())
        
        full_name_constructed = f"{last_name} {first_name} {patronymic}".strip()
        full_name_hemis = format_uzbek_name((s_data.get("short_name") or "").strip()) # Hemis 'short_name' is often initials

        # Robust choice: Construct full name if it has fewer initials
        def count_initials(name):
            return len(re.findall(r'\b[A-Z]\.', name))
            
        if count_initials(full_name_constructed) <= count_initials(full_name_hemis) and len(full_name_constructed) > 5:
            best_full_name = full_name_constructed
        else:
            best_full_name = full_name_hemis or "Talaba"

        update_data = {
            "full_name": best_full_name,
            "short_name": first_name or best_full_name.split()[0],
            "hemis_id": hemis_id,
            "group_number": s_data.get("group", {}).get("name", group_name),
            "image_url": s_data.get("image"),
            
            # Faculty/Specialty
            "faculty_name": s_data.get("department", {}).get("name"),
            "specialty_name": s_data.get("specialty", {}).get("name"),
            
            # Education Details
            "level_name": s_data.get("level", {}).get("name"),
            "education_form": s_data.get("educationForm", {}).get("name"),
            "education_type": s_data.get("educationType", {}).get("name"),
            "payment_form": s_data.get("paymentForm", {}).get("name"),
            "student_status": s_data.get("studentStatus", {}).get("name") or StudentStatus.ACTIVE.value,
            
            "university_id": 1,
            "is_active": True
        }
        
        # Check if student exists by LOGIN (Unique Constraint)
        stmt = select(Student).where(Student.hemis_login == login)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing and hemis_id:
            # Fallback: Check by HEMIS ID if login didn't match (e.g. login changed?)
            stmt = select(Student).where(Student.hemis_id == hemis_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
        
        if existing:
            # Update fields
            # Update fields
            for k, v in update_data.items():
                # SAFETY: Don't overwrite custom images (static/uploads) with HEMIS URL
                if k == "image_url":
                    if existing.image_url and "static/uploads" in existing.image_url:
                        continue
                setattr(existing, k, v)
        else:
            # Create new
            new_student = Student(
                hemis_login=login,
                **update_data
            )
            session.add(new_student)

if __name__ == "__main__":
    asyncio.run(main())
