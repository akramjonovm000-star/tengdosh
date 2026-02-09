from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from services.hemis_service import HemisService
from api.dependencies import get_current_student
from database.models import Student
from database.db_connect import get_session
from services.university_service import UniversityService
from typing import Any

router = APIRouter()

@router.get("/survey")
async def get_student_surveys(
    student: Student = Depends(get_current_student)
):
    token = getattr(student, 'hemis_token', None)
    if not token:
        raise HTTPException(status_code=401, detail="No HEMIS token found")
    
    base_url = UniversityService.get_api_url(student.hemis_login)
    resp = await HemisService.get_student_surveys(token, base_url=base_url)
    if resp is None:
        raise HTTPException(status_code=500, detail="Failed to fetch surveys from HEMIS")
    
    return resp

@router.post("/survey-start")
async def start_survey(
    survey_id: int = Body(..., embed=True),
    student: Student = Depends(get_current_student)
):
    token = getattr(student, 'hemis_token', None)
    if not token:
        raise HTTPException(status_code=401, detail="No HEMIS token found")
    
    base_url = UniversityService.get_api_url(student.hemis_login)
    resp = await HemisService.start_student_survey(token, survey_id, base_url=base_url)
    if resp is None:
        raise HTTPException(status_code=500, detail="Failed to start survey in HEMIS")
    
    return resp

@router.post("/survey-answer")
async def submit_answer(
    question_id: int = Body(...),
    button_type: str = Body(...),
    answer: Any = Body(...),
    student: Student = Depends(get_current_student)
):
    token = getattr(student, 'hemis_token', None)
    if not token:
        raise HTTPException(status_code=401, detail="No HEMIS token found")
    
    base_url = UniversityService.get_api_url(student.hemis_login)
    resp = await HemisService.submit_survey_answer(
        token, 
        question_id, 
        button_type, 
        answer,
        base_url=base_url
    )
    if resp is None:
        raise HTTPException(status_code=500, detail="Failed to submit answer to HEMIS")
    
    return resp

@router.post("/survey-finish")
async def finish_survey(
    quiz_rule_id: int = Body(..., embed=True),
    student: Student = Depends(get_current_student)
):
    token = getattr(student, 'hemis_token', None)
    if not token:
        raise HTTPException(status_code=401, detail="No HEMIS token found")
    
    base_url = UniversityService.get_api_url(student.hemis_login)
    resp = await HemisService.finish_student_survey(token, quiz_rule_id, base_url=base_url)
    if resp is None:
        raise HTTPException(status_code=500, detail="Failed to finish survey in HEMIS")
    
    return resp
