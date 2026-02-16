from fastapi import APIRouter, HTTPException, Request, Depends, Query
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse
import httpx
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from database.db_connect import get_session
from database.models import Student, Staff, StaffRole, University
from config import HEMIS_CLIENT_ID, HEMIS_CLIENT_SECRET, HEMIS_REDIRECT_URL, HEMIS_AUTH_URL, HEMIS_TOKEN_URL, BOT_USERNAME
from services.hemis_service import HemisService
from api.schemas import StudentProfileSchema # Re-use schemas
from utils.academic import get_or_create_academic_context

router = APIRouter(prefix="/oauth", tags=["OAuth"])
authlog_router = APIRouter(tags=["AuthLog"])
logger = logging.getLogger(__name__)

from api.security import limiter, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from utils.encryption import encrypt_data
from datetime import timedelta

@router.get("/login")
@limiter.limit("10/minute")
async def oauth_login(
    request: Request,
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
        return await authlog_callback(request=request, code=code, error=error, state=current_state, db=db)

    # Use 'state' parameter to pass source_role
    redirect_url = HemisService.generate_auth_url(state=current_state, role=role)
    return RedirectResponse(redirect_url)

@authlog_router.get("/")
@authlog_router.get("/authlog")
@authlog_router.get("/oauth/login")
@limiter.limit("20/minute")
async def authlog_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None, state: str = "mobile", db: AsyncSession = Depends(get_session)):
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
    # Explicitly use OAuth endpoint as per instruction
    # [FIX] Set to False to allow Fallback: REST -> OAuth (More robust for Staff)
    me = await HemisService.get_me(access_token, base_url=base_url, use_oauth_endpoint=False)
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
        
        # [FIX] Use 'name' as primary source if available (standard OneID pattern)
        # Fallback to manual concatenation if 'name' is missing
        from utils.text_utils import format_uzbek_name
        
        full_name = me.get("name")
        if not full_name:
            full_name = format_uzbek_name(f"{me.get('surname', '')} {me.get('firstname', '')} {me.get('fathername', '')}".strip())
        else:
            full_name = format_uzbek_name(full_name.strip())
            
        image_url = me.get("picture") or me.get("picture_full") or me.get("image") or me.get("image_url")
        university_id = me.get("university_id")
        
        if not student:
            student = Student(
                full_name=full_name,
                hemis_login=h_login,
                hemis_id=h_id,
                # hemis_token=access_token, # DISABLED
                # hemis_refresh_token=refresh_token, # DISABLED
                # token_expires_at=token_expires_at, # DISABLED
                image_url=image_url
            )
            db.add(student)
            await db.commit()
            await db.refresh(student)
        else:
            # student.hemis_token = access_token # DISABLED
            # student.hemis_refresh_token = refresh_token # DISABLED
            # student.token_expires_at = token_expires_at # DISABLED
            # FORCE UPDATE info
            student.full_name = full_name
            if image_url:
                student.image_url = image_url
            
            # [FIX] Map external university_id to local university_id safely
            u_id = me.get("university_id")
            if u_id:
                try:
                    u_id_int = int(u_id)
                    if u_id_int == 395 or "jmcu" in base_url:
                        student.university_id = 1
                    else:
                        # Only assign if it exists in our DB to avoid IntegrityError
                        exists = await db.scalar(select(University.id).where(University.id == u_id_int))
                        if exists:
                            student.university_id = u_id_int
                        else:
                            logger.warning(f"University ID {u_id_int} not found in local DB. Skipping FK assignment.")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid university_id format for student: {u_id}")
            
            await db.commit()
            
            # [NEW] Enhanced Sync with REST API (for Faculty/Group info)
            # We must pass the token manually now since it's not in DB
            rest_me = await HemisService.get_me(access_token, base_url=base_url, use_oauth_endpoint=False)
            if rest_me:
                logger.info(f"DEBUG: Syncing academic info from REST profile for student {student.id}")
                logger.info(f"DEBUG: REST Profile Role Check: {rest_me.get('roles')}")
                student.university_name = rest_me.get("university", {}).get("name") if isinstance(rest_me.get("university"), dict) else rest_me.get("university_name")
                student.faculty_name = rest_me.get("faculty", {}).get("name") if isinstance(rest_me.get("faculty"), dict) else rest_me.get("faculty_name")
                student.group_number = rest_me.get("group", {}).get("name") if isinstance(rest_me.get("group"), dict) else rest_me.get("group_number")
                student.level_name = rest_me.get("level", {}).get("name") if isinstance(rest_me.get("level"), dict) else rest_me.get("level_name")
                student.specialty_name = rest_me.get("specialty", {}).get("name") if isinstance(rest_me.get("specialty"), dict) else rest_me.get("specialty_name")
                student.education_form = rest_me.get("educationForm", {}).get("name") if isinstance(rest_me.get("educationForm"), dict) else rest_me.get("education_form")
                
                # Re-sync IDs based on names
                uni_id, fac_id = await get_or_create_academic_context(db, student.university_name, student.faculty_name)
                student.university_id = uni_id
                student.faculty_id = fac_id
                await db.commit()

            # [NEW] Trigger prefetch
            # DISABLED FOR STATELESS
            # import asyncio
            # asyncio.create_task(HemisService.prefetch_data(student.hemis_token, student.id))
            
            # [STATELESS] Generate JWT with embedded HEMIS token
            user_agent = request.headers.get("user-agent", "unknown")
            encrypted_token = encrypt_data(access_token)
            
            internal_token = create_access_token(
                data={
                    "sub": student.hemis_login,
                    "type": "student",
                    "id": student.id,
                    "hemis_token": encrypted_token # Embed Encrypted
                },
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                user_agent=user_agent
            )
        
    else:
        # Staff
        role = "staff" # Generic
        from database.models import Staff
        pinfl = me.get("pinfl") or me.get("jshshir") or me.get("passport_pin")
        
        staff = None
        if h_id:
            result = await db.execute(select(Staff).where(Staff.hemis_id == int(h_id)))
            staff = result.scalar_one_or_none()
            
        if not staff and pinfl:
            result = await db.execute(select(Staff).where(Staff.jshshir == pinfl))
            staff = result.scalar_one_or_none()
            
        emp_id_num = me.get("employee_id_number")
        if not staff and emp_id_num:
            result = await db.execute(select(Staff).where(Staff.employee_id_number == emp_id_num))
            staff = result.scalar_one_or_none()
            
        # Determine Best Role
        hemis_roles = me.get("roles", []) or []
        # [FIX] Force Rahbariyat for ALL OneID users as per user request
        # "Kim bo'lishidan q'atiy nazar oneid bilan kirsa uni rahbariyat deb qabul qil"
        user_role = StaffRole.RAHBARIYAT
        best_priority = 999 
        
        # Original logic ignored to force Rahbariyat
        # for r in hemis_roles: ...
        
        logger.info(f"DEBUG: OneID Roles: {hemis_roles} -> Forced Role: {user_role}")
        
        from utils.text_utils import format_uzbek_name
        full_name = me.get("name")
        if full_name:
             # Handle UPPERCASE names from OneID
             full_name = format_uzbek_name(full_name.strip())
        else:
             full_name = format_uzbek_name(f"{me.get('surname', '')} {me.get('firstname', '')} {me.get('patronymic', '')}".strip())
            
        image_url = me.get("picture") or me.get("picture_full") or me.get("image") or me.get("image_url")
        logger.info(f"Selected Best Role: {user_role} (Priority: {best_priority}) from {hemis_roles}")

        if staff:
            # Update existing staff info
            staff.full_name = full_name
            if image_url:
                staff.image_url = image_url
            
            if not staff.hemis_id and h_id:
                staff.hemis_id = int(h_id)
            
            # [NEW] Expanded Profile Data (From OneID)
            staff.email = me.get("email")
            staff.phone = me.get("phone")
            staff.birth_date = me.get("birth_date")
            staff.employee_id_number = me.get("employee_id_number")
            
            # Extract Department and Position
            # 1. Try 'staffPosition' object
            staff_position_obj = me.get("staffPosition")
            if staff_position_obj and isinstance(staff_position_obj, dict):
                staff.position = staff_position_obj.get("name")
            
            # 2. Try 'departments' array (First verified department)
            departments = me.get("departments", [])
            if departments and isinstance(departments, list):
                first_dept = departments[0]
                if isinstance(first_dept, dict):
                     dept_info = first_dept.get("department", {})
                     if isinstance(dept_info, dict):
                         staff.department = dept_info.get("name")
                         
                     # Fallback position if not set
                     if not staff.position:
                         sp = first_dept.get("staffPosition", {})
                         if isinstance(sp, dict):
                             staff.position = sp.get("name")

            # [FIX] Force Rahbariyat for ALL Staff users as per user request
            staff.role = StaffRole.RAHBARIYAT

            # Force Rahbariyat for specific employee_id if needed (Safety Net)
            if staff.employee_id_number == "3952111037": # User's specific ID
                staff.role = "rahbariyat"

            await db.commit()
            # [NEW] Save Token
            # staff.hemis_token = access_token # DISABLED
            u_id = me.get("university_id")
            if u_id:
                try:
                    u_id_int = int(u_id)
                    # Map JMCU (395) -> 1
                    if u_id_int == 395 or "jmcu" in base_url:
                        staff.university_id = 1
                    else:
                        # Only assign if it exists in our DB to avoid IntegrityError
                        exists = await db.scalar(select(University.id).where(University.id == u_id_int))
                        if exists:
                            staff.university_id = u_id_int
                        else:
                            logger.warning(f"University ID {u_id_int} not found in local DB for staff. Skipping.")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid university_id format for staff: {u_id}")
                 
            await db.commit()
            
            # [STATELESS] Generate JWT with embedded HEMIS token
            user_agent = request.headers.get("user-agent", "unknown")
            encrypted_token = encrypt_data(access_token)
            
            internal_token = create_access_token(
                data={
                    "sub": str(h_id), 
                    "type": "staff", 
                    "id": staff.id,
                    "hemis_token": encrypted_token # Embed Encrypted
                },
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                user_agent=user_agent
            )
        else:
            # Auto-register Staff
            logger.info(f"Auto-registering new staff: {h_id} - {me.get('firstname')} {me.get('surname')}")
            
            uni_id_final = None
            u_id_raw = me.get("university_id")
            if u_id_raw:
                try:
                    u_id_int = int(u_id_raw)
                    if u_id_int == 395 or "jmcu" in base_url:
                        uni_id_final = 1
                    else:
                        # Verify existence
                        exists = await db.scalar(select(University.id).where(University.id == u_id_int))
                        if exists: uni_id_final = u_id_int
                except: pass

from utils.encryption import encrypt_data

            staff = Staff(
                hemis_id=int(h_id) if h_id else None,
                full_name=full_name,
                image_url=image_url,
                jshshir=pinfl or "",
                role=user_role,
                phone=me.get("phone"),
                is_active=True,
                hemis_token=encrypt_data(access_token), # [NEW] Encrypted
                # hemis_password=None, # [DISABLED] Privacy
                university_id=uni_id_final
            )
            db.add(staff)
            await db.commit()
            await db.refresh(staff)
            
            # [STATELESS] Generate JWT with embedded HEMIS token
            user_agent = request.headers.get("user-agent", "unknown")
            encrypted_token = encrypt_data(access_token)
            
            internal_token = create_access_token(
                data={
                    "sub": str(h_id), 
                    "type": "staff", 
                    "id": staff.id,
                    "hemis_token": encrypted_token # Embed Encrypted
                },
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                user_agent=user_agent
            )

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
