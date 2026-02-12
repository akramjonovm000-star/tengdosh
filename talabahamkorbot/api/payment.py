from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from services.payment_service import PaymentService, PaymeHandler, PaymeException
from services.hemis_service import HemisService 
from api.dependencies import get_current_student, get_db, get_current_token
from database.db_connect import AsyncSessionLocal
from database.models import Student
from config import PAYME_KEY

router = APIRouter(tags=["Payment"])
security = HTTPBasic()

@router.get("/payme-url")
def get_payme_url(amount: int = 10000, current_student: Student = Depends(get_current_student)):
    """
    Get Payme Checkout URL for Premium Subscription
    """
    import time
    # Unique order ID
    order_id = f"prem_{current_student.id}_{int(time.time())}"
    
    # Temporarily redirect to Coming Soon page
    return {
        "success": True,
        "url": "https://tengdosh.uzjoku.uz/static/payment_soon.html",
        "order_id": order_id
    }
    """
    url = PaymentService.generate_payme_url(amount, order_id)
    
    return {
        "success": True,
        "url": url,
        "order_id": order_id
    }
    """
    
@router.get("/subsidy")
async def get_rent_subsidy(
    year: int = None,
    student = Depends(get_current_student)
):
    """
    Get rent subsidy report (Ijara).
    """
    token = student.hemis_token
    # If student has no token (masquerade/staff case without hemis link?), handle gracefully?
    # Usually hemis_token should be present.
    
    data = await HemisService.get_rent_subsidy_report(token, edu_year=year)
    
    if data is None:
        raise HTTPException(status_code=401, detail="HEMIS Authentication Failed")
        
    return {
        "success": True,
        "data": data
    }

@router.post("/payme")
async def payme_webhook(
    payload: dict,
    credentials: HTTPBasicCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
):
    # ... existing Payme logic ...
    # 1. Authorize
    if credentials.password != PAYME_KEY:
         return {
             "id": payload.get("id"),
             "result": None,
             "error": {"code": -32504, "message": "Access denied"}
         }

    # 2. Handle
    handler = PaymeHandler(session)
    method = payload.get("method")
    params = payload.get("params", {})
    
    try:
        result = await handler.handle(method, params)
        return {"result": result, "id": payload.get("id")}
    except PaymeException as e:
        return {
            "result": None,
            "id": payload.get("id"),
            "error": {"code": int(e.code), "message": e.message}
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "result": None,
            "id": payload.get("id"),
            "error": {"code": -32400, "message": "System Error"}
        }

# --- CLICK ---
from fastapi import Form
from services.payment_service import ClickHandler

@router.get("/click-url")
def get_click_url(amount: int = 10000, current_student: Student = Depends(get_current_student)):
    import time
    order_id = f"prem_{current_student.id}_{int(time.time())}"
    # Temporarily redirect to Coming Soon page
    return {
        "success": True,
        "url": "https://tengdosh.uzjoku.uz/static/payment_soon.html",
        "order_id": order_id
    }
    """
    url = ClickHandler.generate_url(amount, order_id)
    return {
        "success": True,
        "url": url,
        "order_id": order_id
    }
    """

@router.post("/click")
async def click_webhook(
    click_trans_id: str = Form(...),
    service_id: str = Form(...),
    click_paydoc_id: str = Form(...),
    merchant_trans_id: str = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    params = {
       "click_trans_id": click_trans_id,
       "service_id": service_id,
       "click_paydoc_id": click_paydoc_id,
       "merchant_trans_id": merchant_trans_id,
       "amount": amount,
       "action": action,
       "error": error,
       "error_note": error_note,
       "sign_time": sign_time,
       "sign_string": sign_string
    }
    
    handler = ClickHandler(session)
    result = await handler.handle(params)
    
    # Ensure required fields in response
    result["click_trans_id"] = click_trans_id
    result["merchant_trans_id"] = merchant_trans_id
    # service_id?
    
    return result

# --- UZUM ---
from services.payment_service import UzumHandler
from config import UZUM_SECRET_KEY, UZUM_SERVICE_ID

@router.get("/uzum-url")
def get_uzum_url(amount: int = 10000, current_student: Student = Depends(get_current_student)):
    import time
    order_id = f"prem_{current_student.id}_{int(time.time())}"
    # Temporarily redirect to Coming Soon page
    return {
        "success": True,
        "url": "https://tengdosh.uzjoku.uz/static/payment_soon.html",
        "order_id": order_id
    }
    """
    url = UzumHandler.generate_url(amount, order_id)
    return {
        "success": True,
        "url": url,
        "order_id": order_id
    }
    """

@router.post("/uzum")
async def uzum_webhook(
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    # Authorization logic (Basic Auth or Header)
    # Checking Authorization header manually or via Depends
    auth_header = request.headers.get("Authorization")
    # if auth_header... check
    
    # Simple check for demo:
    # If using Basic Auth:
    # username = ServiceId, password = Secret
    
    handler = UzumHandler(session)
    result = await handler.handle(payload)
    return result


