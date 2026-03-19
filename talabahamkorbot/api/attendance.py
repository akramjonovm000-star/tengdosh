from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connect import get_db
from database.models import Student
from api.dependencies import get_current_user_direct, require_action_token
import aiohttp
from pydantic import BaseModel

router = APIRouter()

class QRScanRequest(BaseModel):
    qr_code: str

@router.post("/qr-scan")
async def scan_qr_attendance(
    request: QRScanRequest,
    # token: str = Depends(require_action_token),
    student: Student = Depends(get_current_user_direct),
    db: AsyncSession = Depends(get_db)
):
    """
    Skaner qilingan QR kodni HEMIS tizimiga yuboradi.
    """
    qr_code = request.qr_code
    hemis_token = getattr(student, "hemis_token", None)
    
    if not hemis_token:
        # Tring to get from DB if not in ClassVar, but typically it depends on how auth works
        raise HTTPException(status_code=401, detail="HEMIS token topilmadi. Qaytadan tizimga kiring.")
        
    url = "https://student.jmcu.uz/rest/v1/student/qr-attendance"
    headers = {
        "Authorization": f"Bearer {hemis_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "token": hemis_token,
        "code": qr_code
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                print(f"[QR_ATTENDANCE] HEMIS Response: {result}")
                
                # Hemis typically returns {"success": true, "message": "..."}
                if response.status == 200 and result.get("success"):
                    return {"success": True, "message": result.get("message", "Davomatga muvaffaqiyatli yozildingiz")}
                else:
                    error_msg = result.get("error", "Kutilmagan xatolik yuz berdi")
                    return {"success": False, "message": error_msg}
        except Exception as e:
            print(f"[QR_ATTENDANCE] Error calling HEMIS: {e}")
            raise HTTPException(status_code=500, detail="HEMIS tizimiga ulanishda xatolik yuz berdi")
