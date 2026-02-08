from fastapi import APIRouter, HTTPException, Request, Depends, Query
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse
import httpx
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from database.db_connect import get_session
from database.models import Student, Staff, StaffRole
from config import HEMIS_CLIENT_ID, HEMIS_CLIENT_SECRET, HEMIS_REDIRECT_URL, HEMIS_AUTH_URL, HEMIS_TOKEN_URL, BOT_USERNAME
from services.hemis_service import HemisService
from api.schemas import StudentProfileSchema # Re-use schemas

router = APIRouter(prefix="/oauth", tags=["OAuth"])
authlog_router = APIRouter(tags=["AuthLog"])
logger = logging.getLogger(__name__)

@router.get("/login")
async def oauth_login(
    source: str = "mobile", 
    role: str = "student",
    code: Optional[str] = None, 
    error: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Redirects user to HEMIS OAuth Authorization Page.
    ALSO handles Callback if User mistakenly set Redirect URI to this endpoint.
    """
    # Combine source and role into state
    current_state = state or f"{source}_{role}"

    # LOOP PREVENTION: If code is present, treat as callback!
    if code or error:
        logger.warning(f"OAuth Login endpoint received 'code' - Handling as callback. State: {current_state}")
        return await authlog_callback(code=code, error=error, state=current_state, db=db)

    # Use 'state' parameter to pass source_role
    redirect_url = HemisService.generate_auth_url(state=current_state, role=role)
    return RedirectResponse(redirect_url)

@authlog_router.get("/")
@authlog_router.get("/authlog")
@authlog_router.get("/oauth/login")
async def authlog_callback(code: Optional[str] = None, error: Optional[str] = None, state: str = "mobile", db: AsyncSession = Depends(get_session)):
    t0 = time.time()
    """
    Handles the callback from HEMIS (redirected via Nginx /authlog OR Root)
    """
    if not code and not error:
         return {"status": "active", "service": "TalabaHamkor API", "version": "1.0.0"}

    if error:
         return HTMLResponse(content=f"<h1>Avtorizatsiya rad etildi: {error}</h1>", status_code=400)

    # Determine domain from state
    base_url = "https://student.jmcu.uz"
    if "_staff" in state:
        base_url = "https://hemis.jmcu.uz"

    logger.info(f"AuthLog: Exchanging code {code[:5]} using {base_url}...")
    
    token_data, error_msg = await HemisService.exchange_code(code, base_url=base_url)
    t1 = time.time()
    logger.info(f"AuthLog: Token Exchange took {t1 - t0:.2f}s")

    if error_msg:
         return HTMLResponse(content=f"<h1>Login Xatoligi: {error_msg}</h1>", status_code=400)

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
    logger.info(f"AuthLog: Fetching profile for token {access_token[:10]} using {base_url}...")
    me = await HemisService.get_me(access_token, base_url=base_url)
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

            # [NEW] Prefetch Data
            import asyncio
            asyncio.create_task(HemisService.prefetch_data(student.hemis_token, student.id))
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
             # Auto-register Staff
             logger.info(f"Auto-registering new staff: {h_id} - {me.get('firstname')} {me.get('surname')}")
             
             # Map roles
             hemis_roles = me.get("roles", []) or []
             user_role = StaffRole.TEACHER
             
             # Simple mapping (expand as needed)
             role_map = {
                 "tutor": StaffRole.TYUTOR,
                 "teacher": StaffRole.TEACHER,
                 "dean": StaffRole.DEKAN,
                 "department_head": StaffRole.KAFEDRA_MUDIRI
             }
             
             for r in hemis_roles:
                 if isinstance(r, dict): r_code = r.get("code")
                 else: r_code = str(r)
                 
                 if r_code in role_map:
                     user_role = role_map[r_code]
                     break
             
             staff = Staff(
                 hemis_id=int(h_id) if h_id else None,
                 full_name=f"{me.get('surname', '')} {me.get('firstname', '')} {me.get('patronymic', '')}".strip(),
                 jshshir=pinfl or "",
                 role=user_role,
                 phone=me.get("phone"),
                 is_active=True
             )
             db.add(staff)
             await db.commit()
             await db.refresh(staff)
             
             internal_token = f"staff_id_{staff.id}"

    # 4. Return HTML
    
    if state.startswith("bot"):
        # Redirect to Telegram Bot with Deep Link
        telegram_link = f"https://t.me/{BOT_USERNAME}?start=login__{internal_token}"
        
        # ... (html_content omitted for brevity, keeping same logic)
        return HTMLResponse(content=f"<html><head><meta http-equiv=\"refresh\" content=\"0; url={telegram_link}\"></head><body>Redirecting to bot...</body></html>")
        
    else:
        # Default: Mobile App Deep Link
        # Instead of RedirectResponse, return HTML with JS redirect + Manual Button
        # This handles cases where browser blocks auto-redirect or if user wants to see success message
        
        deep_link = f"talabahamkor://auth?token={internal_token}&status=success"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Muvaffaqiyatli Kirildi</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; text-align: center; padding: 40px 20px; background-color: #f5f5f7; color: #333; }}
                .container {{ background: white; padding: 40px; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }}
                h1 {{ color: #2ecc71; margin-bottom: 10px; }}
                p {{ color: #666; font-size: 16px; margin-bottom: 30px; }}
                .btn {{ display: inline-block; background-color: #007aff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px; transition: background 0.2s; }}
                .btn:active {{ transform: scale(0.98); opacity: 0.9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div style="font-size: 60px; margin-bottom: 20px;">✅</div>
                <h1>Muvaffaqiyatli Kirildi</h1>
                <p>Sizning hisobingiz tasdiqlandi. Ilovaga qaytish uchun quyidagi tugmani bosing.</p>
                <a href="{deep_link}" class="btn">Ilovaga Qaytish</a>
            </div>
            <script>
                // Try auto-redirect after 1 second
                setTimeout(function() {{
                    window.location.href = "{deep_link}";
                }}, 1000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
