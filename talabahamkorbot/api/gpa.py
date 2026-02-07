from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.dependencies import get_current_student, get_db
from api.schemas import GPAResultSchema
from database.models import Student
from services.hemis_service import HemisService
from services.gpa_calculator import GPACalculator

router = APIRouter()

@router.get("/semester", response_model=GPAResultSchema)
async def get_semester_gpa(
    semester_id: Optional[str] = Query(None, description="Semester Code (e.g. 11, 12). If empty, uses current semester."),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Weighted GPA for a specific semester.
    """
    semester_id_provided = semester_id is not None
    token = getattr(student, 'hemis_token', None)
    if not token:

        # Return empty / zero 
        return {
            "gpa": 0.0,
            "total_credits": 0.0,
            "total_points": 0.0,
            "subjects": []
        }

    # 0. Check Auth Status
    if await HemisService.check_auth_status(token) == "AUTH_ERROR":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    # If no semester provided, try to find current
    if not semester_id:
        me_data = await HemisService.get_me(token)
        if me_data:
            sem = me_data.get("semester", {})
            semester_id = str(sem.get("code") or sem.get("id") or "11")
        else:
            semester_id = "11"

    # Fetch subjects
    subjects = await HemisService.get_student_subject_list(token, semester_code=semester_id, student_id=student.id)
    if not subjects:
        subjects = []

    # Calculate
    result = GPACalculator.calculate_gpa(subjects)
    
    # FALLBACK LOGIC:
    # If using current semester (auto-detected) AND result is empty (0 credits),
    # try to fetch the previous semester. This handles "Start of Semester" cases.
    if result.total_credits == 0 and not semester_id_provided:
        try:
            prev_code = str(int(semester_id) - 1)
            # Fetch previous subjects
            prev_subjects = await HemisService.get_student_subject_list(token, semester_code=prev_code, student_id=student.id)
            if prev_subjects:
                prev_result = GPACalculator.calculate_gpa(prev_subjects)
                if prev_result.total_credits > 0:
                    return prev_result.dict()
        except:
             pass # Fail silently and return original zero result

    # Convert to Schema
    return result.dict()

@router.get("/cumulative", response_model=GPAResultSchema)
async def get_cumulative_gpa(
    retake_policy: str = Query("latest", regex="^(latest|best)$"),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Cumulative GPA across ALL semesters.
    """
    token = getattr(student, 'hemis_token', None)
    if not token:

        return {
            "gpa": 0.0,
            "total_credits": 0.0,
            "total_points": 0.0,
            "subjects": []
        }

    # 0. Check Auth Status
    if await HemisService.check_auth_status(token) == "AUTH_ERROR":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    # We need to fetch ALL semesters subjects.
    # Since HemisService.get_student_subject_list takes semester_code, 
    # we need to iterate all semesters or finding an endpoint that returns all?
    # Usually HEMIS has `education/result-list` or similar, but let's stick to safe iteration.
    
    # 1. Get Me to find current semester
    me_data = await HemisService.get_me(token)
    current_sem_code = 11
    if me_data:
        sem = me_data.get("semester", {})
        try:
            current_sem_code = int(sem.get("code") or sem.get("id") or 11)
        except: pass
    
    if current_sem_code < 11: current_sem_code = 11

    # 2. Iterate from 11 to current
    # Ideally optimize this to be parallel
    import asyncio
    
    tasks = []
    for code in range(11, current_sem_code + 2): # Check +1 just in case
        tasks.append(HemisService.get_student_subject_list(token, semester_code=str(code), student_id=student.id))
        
    results = await asyncio.gather(*tasks)
    
    all_subjects = []
    for r in results:
        if r: all_subjects.extend(r)
        
    # Calculate Cumulative
    result = GPACalculator.calculate_cumulative(all_subjects, retake_policy=retake_policy)
    
    return result.dict()
