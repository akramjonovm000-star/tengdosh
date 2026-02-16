from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_current_student, get_db
from database.models import Student
from services.token_service import TokenService
import logging

router = APIRouter(prefix="/security/tokens", tags=["Security"])
logger = logging.getLogger(__name__)

@router.post("/request")
async def request_tokens(
    count: int = 50, # Default count
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Request a batch of implementation tokens (shifrs).
    Maximum 500 per request.
    """
    if count > 500:
        count = 500
    if count < 1:
        count = 1
        
    try:
        tokens = await TokenService.generate_batch(db, student.id, "student", count)
        return {
            "success": True, 
            "tokens": tokens, 
            "count": len(tokens),
            "message": "Tokens generated successfully"
        }
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")
