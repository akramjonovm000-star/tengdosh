from fastapi import APIRouter, Depends, Query, HTTPException
from api.schemas import HemisLoginRequest
from services.hemis_service import HemisService
from services.university_service import UniversityService
from api.dependencies import get_current_student
from database.models import Student
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/direct")
async def debug_hemis_direct(creds: HemisLoginRequest):
    """
    Debug Endpoint 1: Direct Authentication + Immediate Service Call
    Isolates: Is the token valid? Is HemisService working?
    """
    base_url = UniversityService.get_api_url(creds.login)
    logger.info(f"DEBUG: Authenticating {creds.login} against {base_url}")
    
    token, error = await HemisService.authenticate(creds.login, creds.password, base_url=base_url)
    if not token:
        return {"success": False, "step": "auth", "error": error}
        
    logger.info(f"DEBUG: Auth success. Token: {token[:15]}...")
    
    # Immediately try to fetch something
    me_data = await HemisService.get_me(token, base_url=base_url)
    if not me_data:
        # Check why
        auth_status = await HemisService.check_auth_status(token, base_url=base_url)
        return {"success": False, "step": "get_me", "error": f"Failed to fetch profile. Auth Status: {auth_status}"}
        
    return {
        "success": True, 
        "token_snippet": token[:20],
        "profile_name": me_data.get("full_name"),
        "message": "Direct HEMIS call works. Token is valid."
    }

@router.get("/propagation")
async def debug_propagation(student: Student = Depends(get_current_student)):
    """
    Debug Endpoint 2: Dependency Injection Check
    Isolates: Is the token correctly injected into the Student object?
    """
    token = getattr(student, 'hemis_token', None)
    
    status = "MISSING"
    length = 0
    token_val = None
    
    if token:
        status = "PRESENT"
        length = len(token)
        token_val = token[:10] + "..."
        
    # Validating the token against HEMIS (if present)
    hemis_check = "SKIPPED"
    if token:
        base_url = UniversityService.get_api_url(student.hemis_login)
        check = await HemisService.check_auth_status(token, base_url=base_url)
        hemis_check = check
        
    return {
        "student_id": student.id,
        "hemis_token_status": status,
        "token_snippet": token_val,
        "token_length": length,
        "hemis_validation": hemis_check,
        "injected_correctly": status == "PRESENT"
    }
