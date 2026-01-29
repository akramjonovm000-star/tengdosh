from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
import httpx
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database.db_connect import get_session
from database.models import Student, Staff, StaffRole
from config import HEMIS_CLIENT_ID, HEMIS_CLIENT_SECRET, HEMIS_REDIRECT_URL, HEMIS_AUTH_URL, HEMIS_TOKEN_URL, BOT_USERNAME
from services.hemis_service import HemisService
from api.schemas import StudentProfileSchema # Re-use schemas

router = APIRouter(prefix="/oauth", tags=["OAuth"])
authlog_router = APIRouter(tags=["AuthLog"])
logger = logging.getLogger(__name__)

@router.get("/login")
async def oauth_login(source: str = "mobile"):
    """
    Redirects user to HEMIS OAuth Authorization Page
    source: 'mobile' (default) or 'bot'
    """
    # Use 'state' parameter to pass source
    # Use 'state' parameter to pass source
    # state = source
    redirect_url = HemisService.generate_auth_url(state=source)
    return RedirectResponse(redirect_url)

@authlog_router.get("/authlog")
async def authlog_callback(code: str, state: str = "mobile", db: AsyncSession = Depends(get_session)):
    """
    Handles the callback from HEMIS (redirected via Nginx /authlog)
    """
    logger.info(f"OAuth Callback received code: {code}, state: {state}")
    
    # 1. Exchange Code for Exchange Token
    import time
    t0 = time.time()
    logger.info(f"AuthLog: Exchanging code {code[:5]}...")
    
    token_data = await HemisService.exchange_code(code)
    t1 = time.time()
    logger.info(f"AuthLog: Token Exchange took {t1 - t0:.2f}s")

    if not token_data:
        return HTMLResponse(content="<h1>Login Xatoligi: Token olinmadi</h1>", status_code=400)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 0)
    
    # Calculate expiry
    from datetime import datetime, timedelta
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    if not access_token:
         return HTMLResponse(content="<h1>Token olinmadi</h1>", status_code=400)
    
    # 2. Get User Profile with this Token (CRITICAL STEP)
    logger.info(f"AuthLog: Fetching profile for token {access_token[:10]}...")
    me = await HemisService.get_me(access_token)
    t2 = time.time()
    logger.info(f"AuthLog: Get Me took {t2 - t1:.2f}s")
    
    if not me:
         return HTMLResponse(content="<h1>Foydalanuvchi ma'lumotlarini olib bo'lmadi</h1>", status_code=500)
         
    # 3. Save/Update User in DB (Same logic as auth.py)
    h_id = str(me.get("id", ""))
    h_login = me.get("login")
    user_type = me.get("type", "student")
    
    internal_token = ""
    role = "student"
    
    if user_type == "student":
        role = "student"
        result = await db.execute(select(Student).where(Student.hemis_login == h_login))
        student = result.scalar_one_or_none()
        
        full_name = f"{me.get('firstname', '')} {me.get('lastname', '')} {me.get('fathername', '')}".strip()
        
        if not student:
            student = Student(
                full_name=full_name,
                hemis_login=h_login,
                hemis_id=h_id,
                hemis_token=access_token,
                hemis_refresh_token=refresh_token,
                token_expires_at=token_expires_at
            )
            db.add(student)
            await db.commit()
            await db.refresh(student)
        else:
            student.hemis_token = access_token
            student.hemis_refresh_token = refresh_token
            student.token_expires_at = token_expires_at
            # FORCE UPDATE info
            student.full_name = full_name
            # Also update other fields if needed, e.g. if we add university_name here later
            await db.commit()
            
        internal_token = f"student_id_{student.id}"
        
    else:
        # Staff
        role = "staff" # Generic
        from database.models import Staff
        pinfl = me.get("pinfl") or me.get("jshshir")
        
        staff = None
        if h_id:
            result = await db.execute(select(Staff).where(Staff.hemis_id == int(h_id)))
            staff = result.scalar_one_or_none()
            
        if not staff and pinfl:
            result = await db.execute(select(Staff).where(Staff.jshshir == pinfl))
            staff = result.scalar_one_or_none()
            
        if staff:
            if not staff.hemis_id and h_id:
                staff.hemis_id = int(h_id)
            # Staff doesn't have hemis_login column usually, so skip or add if schema changed
            # staff.hemis_login = h_login 
            await db.commit() # Save hemis_id
            
            # Role fallback
            if not staff.role:
                 # If lazy created with no role? (Unlikely)
                 pass
                 
            internal_token = f"staff_id_{staff.id}"
        else:
             # AUTO-REGISTER STAFF if strict policy allows?
             # For now, if not in DB (neither pre-loaded nor lazy-created), we deny.
             return HTMLResponse(content="<h1>Tizimda xodim topilmadi</h1>", status_code=403)

    # 4. Return HTML
    
    if state == "bot":
        # Redirect to Telegram Bot with Deep Link
        # Format: https://t.me/BOT_USERNAME?start=login_TOKEN
        # Note: Telegram start param only allows [a-zA-Z0-9_-], no special chars.
        # internal_token format is "student_id_123", which is safe.
        
        telegram_link = f"https://t.me/{BOT_USERNAME}?start=login__{internal_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Muvaffaqiyatli</title>
            <meta http-equiv="refresh" content="0; url={telegram_link}">
            <style>
                body {{ font-family: sans-serif; text-align: center; padding: 20px; }}
                .btn {{ display: inline-block; padding: 15px 30px; background-color: #0088cc; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>✅ Muvaffaqiyatli!</h1>
            <p>Botga qaytayapsiz...</p>
            <a href="{telegram_link}" class="btn">Botni Ochish</a>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    else:
        # Default: Mobile App Deep Link
        redirect_uri = f"talabahamkor://login?token={internal_token}&role={role}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Muvaffaqiyatli</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; text-align: center; padding: 20px; }}
                .btn {{ display: inline-block; padding: 15px 30px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>✅ Login Muvaffaqiyatli!</h1>
            <p>Ilovaga qaytishingiz mumkin.</p>
            
            <script>
                // Auto redirect
                window.location.href = "{redirect_uri}";
            </script>
            
            <br><br>
            <a href="{redirect_uri}" class="btn">Ilovani Ochish</a>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
