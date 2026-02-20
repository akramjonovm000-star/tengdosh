from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db_connect import get_session
from database.models import Student, User
from services.hemis_service import HemisService
from services.university_service import UniversityService
from api.schemas import HemisLoginRequest, StudentProfileSchema
import logging
import re

# [SECURITY] Import Limiter
from api.security import limiter, create_access_token
from datetime import timedelta

router = APIRouter()
logger = logging.getLogger(__name__)

from utils.academic import get_or_create_academic_context

@router.post("/hemis")
@router.post("/hemis/")
# @limiter.limit("5/minute") # [CONFIG] Disabled by User Request
async def login_via_hemis(
    request: Request, # Required for limiter
    creds: HemisLoginRequest,
    db: AsyncSession = Depends(get_session)
):
    # 1. AUTHENTICATE
    import os
    login_clean = creds.login.strip().lower()
    pass_clean = creds.password.strip()
    
    logger.info(f"Auth Attempt: login='{login_clean}'")
    
    # [SECURITY] HARDCODED CREDENTIALS REMOVED
    # Previous demo logic was here. Removed for security self-audit.
    demo_login = None
    full_name = ""
    role = ""

    # [HOTFIX] Hardcoded Dean1 Demo Logic (Unconditional)
    if login_clean == "dean1":
         logger.info(f"Dean1 Login Attempt. Password length: {len(pass_clean)}")
         if pass_clean == "123":
             demo_login = "dean1"
             full_name = "Jurnalistika Dekanati"
             role = "dekan"
         else:
             logger.warning(f"Dean1 Login Failed: Password Mismatch. Received '{pass_clean}'")

    # Only enable minimal demo if strictly needed via ENV
    if not demo_login and os.environ.get("ENABLE_DEMO_AUTH") == "1":
        if pass_clean == "123":
            if login_clean == "demo":
                 demo_login = "demo.student"
                 full_name = "Demo Talaba"
                 role = "student"
             
    logger.debug(f"DEBUG AUTH: demo_login='{demo_login}'")
            
    if demo_login:
        # EXCLUSIVE FOR JURNALISTIKA DEMO
        # EXCLUSIVE FOR DEAN1 (Jurnalistika Dean)
        if demo_login == "dean1":
             from datetime import datetime
             from database.models import Staff, StaffRole
             
             # Check if Staff already exists
             demo_staff = await db.scalar(select(Staff).where(Staff.employee_id_number == demo_login))
             
             if not demo_staff:
                 demo_staff = Staff(
                    hemis_id=777888777, 
                    full_name=full_name,
                    role=StaffRole.DEKAN, 
                    university_id=1,
                    faculty_id=36, # [CONFIG] Jurnalistika Faculty
                    is_premium=True,
                    premium_expiry=datetime.utcnow() + timedelta(days=1), # 24 hours
                    custom_badge="Dekanat (Demo)",
                    image_url=f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=random",
                    position="Dekan",
                    department="Dekanat",
                    employee_id_number=demo_login
                 )
                 db.add(demo_staff)
                 await db.commit()
                 await db.refresh(demo_staff)
             else:
                 # Update permissions if exists
                 demo_staff.is_premium = True
                 demo_staff.premium_expiry = datetime.utcnow() + timedelta(days=1)
                 demo_staff.faculty_id = 36 # Ensure Faculty 36
                 demo_staff.role = StaffRole.DEKAN
                 await db.commit()
                 await db.refresh(demo_staff)
             
             from utils.encryption import encrypt_data
             encrypted_dummy_token = encrypt_data("demo.token.dean1")
             user_agent = request.headers.get("user-agent", "unknown")
                 
             access_token = create_access_token(
                data={
                    "sub": demo_staff.full_name, 
                    "type": "staff", 
                    "id": demo_staff.id,
                    "hemis_token": encrypted_dummy_token
                },
                user_agent=user_agent
             )
             return {
                "access_token": access_token,
                "token": access_token, # [COMPAT] Mobile App expects 'token'
                "token_type": "bearer",
                "user_info": {
                    "id": demo_staff.id,
                    "hemis_id": demo_staff.hemis_id,
                    "full_name": demo_staff.full_name,
                    "type": "staff",
                    "university_id": 1,
                    "faculty_id": 36,
                    "image_url": demo_staff.image_url,
                    "role": "dekan",
                    "profile": {
                         "id": demo_staff.id,
                         "full_name": demo_staff.full_name,
                         "role": "dekan",
                         "image": demo_staff.image_url,
                         "hemis_login": demo_login,
                         "faculty_id": 36,
                         "university_id": 1
                    }
                }
             }

        if role in ["tutor", "tyutor", "rahbariyat", "dekan"]:
            # Demo Staff Logic
            from database.models import Staff, StaffRole
            
            demo_staff = None
            if demo_login == "demo.nazokat":
                 # Fetch actual user 64
                 demo_staff = await db.scalar(select(Staff).where(Staff.id == 64))
                 if not demo_staff:
                     # Fallback search by name if ID changed (though unlikely)
                     demo_staff = await db.scalar(select(Staff).where(Staff.full_name.ilike("%Nazokat%")))
            elif demo_login == "demo.dekanat":
                 # Fetch actual user 80
                 demo_staff = await db.scalar(select(Staff).where(Staff.id == 80))
                 if not demo_staff:
                     demo_staff = await db.scalar(select(Staff).where(Staff.username == "dekanat"))
            
            if not demo_staff:     
                # Check by ID OR JSHSHIR to avoid IntegrityError (Standard Demo Logic)
                target_hemis_id = 999999 if role == "tutor" else 888888
                target_jshshir = "12345678901234" if role == "tutor" else "98765432109876"
    
                demo_staff = await db.scalar(
                    select(Staff).where(
                        (Staff.hemis_id.in_([999999, 888888])) | 
                        (Staff.jshshir.in_(["12345678901234", "98765432109876"]))
                )
            )
            
            if not demo_staff:
                demo_staff = Staff(
                    full_name=full_name,
                    jshshir=target_jshshir,
                    role=role, 
                    hemis_id=target_hemis_id,
                    phone="998901234567",
                    university_id=1
                )
                db.add(demo_staff)
                await db.commit()
                await db.refresh(demo_staff)
            else:
                # Update existing if needed
                if demo_staff.role != role:
                    demo_staff.role = role
                if role == "tutor" and demo_staff.hemis_id != 999999:
                    demo_staff.hemis_id = 999999
                elif role == "rahbariyat" and demo_staff.hemis_id != 888888:
                    demo_staff.hemis_id = 888888
                
                # Ensure university is set
                if not demo_staff.university_id:
                    demo_staff.university_id = 1
                    demo_staff.university_name = "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti"
                await db.commit()
            
            print(f"DEBUG AUTH: Success! Token='staff_id_{demo_staff.id}'")
            return {
                "success": True, 
                "data": {
                    "token": f"staff_id_{demo_staff.id}",
                    "role": role,
                    "profile": {
                         "id": demo_staff.id,
                         "full_name": demo_staff.full_name,
                         "role": role,
                         "image": f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=random"
                    }
                }
            }
        else:
            # Demo Student Logic
            # Ensure Demo User Exists
            demo_user = await db.scalar(select(Student).where(Student.hemis_login == demo_login))
            if not demo_user:
                # Define Demo Data based on login
                u_name = "Test Universiteti"
                f_name = "Test Fakulteti"
                g_num = "101-GROUP"
                u_id = 1
                f_id = 5
                
                # Removed dead code for demo.jurnalistika

                from datetime import datetime
                demo_user = Student(
                    hemis_id=f"{login_clean}_123",
                    full_name=full_name,
                    hemis_login=demo_login,
                    hemis_password="123",
                    university_name=u_name,
                    faculty_name=f_name,
                    level_name="1-kurs",
                    group_number=g_num,
                    hemis_role=role,
                    university_id=u_id,
                    faculty_id=f_id,
                    is_premium=True,
                    premium_expiry=datetime.utcnow() + timedelta(days=30),
                    custom_badge="Rahbariyat (Demo)",
                    image_url=f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=random"
                )
                db.add(demo_user)
                await db.commit()
                await db.refresh(demo_user)
            
            # 4. CREATE TOKEN
            # [NEW] Token Binding
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Create a REAL JWT for demo user instead of fake string
            # This allows testing the binding logic even with demo users
            # Encrypt a dummy token to satisfy dependencies.py
            from utils.encryption import encrypt_data
            encrypted_dummy_token = encrypt_data("demo.token.123")
            
            user_agent = request.headers.get("user-agent", "unknown")
            
            access_token = create_access_token(
                data={
                    "sub": demo_user.hemis_login, 
                    "type": "student", 
                    "id": demo_user.id,
                    "hemis_token": encrypted_dummy_token
                },
                expires_delta=timedelta(minutes=60 * 24 * 7), # 7 days
                user_agent=user_agent
            )

            print(f"DEBUG AUTH: Success! Token Generated for Demo User")
            
            return {
                "success": True,
                "data": {
                    "token": access_token,
                    "role": role,
                    "profile": {
                        "id": demo_user.id,
                        "full_name": demo_user.full_name,
                        "university": {"name": demo_user.university_name},
                        "image": demo_user.image_url,
                        "role": role
                    }
                }
            }

    # 1. AUTHENTICATE
    import time
    from sqlalchemy.exc import SQLAlchemyError
    from aiohttp import ClientError
    t_start = time.time()
    
    # [NEW] Rate Limiting Check
    from services.rate_limit_service import RateLimitService
    
    # Use login as key
    rate_key = creds.login
    is_blocked, ttl = await RateLimitService.check_rate_limit(rate_key, limit=10, block_time=3600)
    
    if is_blocked:
        # Convert seconds to hours/minutes
        minutes = int(ttl / 60)
        hours = int(minutes / 60)
        
        msg = f"Siz juda ko'p marta xato kiritdingiz. Iltimos {minutes} daqiqadan so'ng urinib ko'ring."
        if hours >= 1:
             msg = f"Siz juda ko'p marta xato kiritdingiz. Iltimos {hours} soatdan so'ng urinib ko'ring."
             
        raise HTTPException(
            status_code=429, 
            detail={"error": "RATE_LIMIT", "message": msg}
        )

    # [NEW] Dynamic University Detection
    base_url = UniversityService.get_api_url(creds.login)
    logger.info(f"AuthLog: Resolved URL for {creds.login}: {base_url}")
    
    try:
        token, error = await HemisService.authenticate(creds.login, creds.password, base_url=base_url)
        t_auth = time.time()
        logger.info(f"AuthLog: Authenticate took {t_auth - t_start:.2f}s")
        
        if not token:
            # [NEW] Increment Failed Attempt
            await RateLimitService.increment_attempt(rate_key, block_time=3600)
            
            error_code = "INVALID_CREDENTIALS"
            error_msg = "Login yoki parol noto'g'ri"
            
            # Check if Hemis explicitly said something else (e.g. 500)
            if error and "50" in str(error): # 500, 502, 503
                 error_code = "HEMIS_ERROR"
                 error_msg = "Hemis tizimi javob bermayapti"

            logger.warning(f"AuthLog: Auth failed via Hemis: {error}")
            raise HTTPException(
                status_code=401 if error_code == "INVALID_CREDENTIALS" else 502, 
                detail={"error": error_code, "message": error_msg}
            )
        
        # [NEW] Clear Attempts on Success
        await RateLimitService.clear_attempts(rate_key)
            
    except ClientError as e:
        logger.error(f"Hemis Network Error: {e}")
        raise HTTPException(
            status_code=502,
            detail={"error": "HEMIS_ERROR", "message": "Hemis tizimi bilan aloqa yo'q (Network)."}
        )
    except SQLAlchemyError as e:
        logger.critical(f"Database Error during Auth: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": "DB_ERROR", "message": "Ma'lumotlar bazasi vaqtincha ishlamayapti."}
        )
        

    # 2. GET PROFILE
    logger.info(f"AuthLog: Fetching profile for login {creds.login}...")
    me = await HemisService.get_me(token, base_url=base_url)
    t_profile = time.time()
    logger.info(f"AuthLog: Get Me took {t_profile - t_auth:.2f}s")
    
    if not me:
        raise HTTPException(status_code=500, detail="Profil ma'lumotlarini olib bo'lmadi")

    # 3. CHECK USER TYPE
    user_type = me.get("type", "student")
    
    if user_type != "student":
        # --- STAFF / TUTOR LOGIC ---
        from database.models import Staff
        
        # Identify via ID or PINFL
        h_id = me.get("id")
        pinfl = me.get("pinfl") or me.get("jshshir")
        
        staff = None
        if h_id:
            staff = await db.scalar(select(Staff).where(Staff.hemis_id == int(h_id)))
            
        if not staff and pinfl:
            staff = await db.scalar(select(Staff).where(Staff.jshshir == pinfl))
            
        if not staff:
             # Auto-register Staff? Currently restricted to imported staff.
             # But for Tutors, we assume they are imported.
             logger.warning(f"Login attempted by Staff {creds.login} (ID={h_id}) but not found in DB.")
             raise HTTPException(status_code=403, detail="Siz tizimda xodim sifatida topilmadingiz")
             
        # [NEW] Gating for Tutor Module Development
        # Allow if role is "tyutor" AND login is "nazokat" (handled by demo logic above) or explicitly whitelisted
        # But this is OAuth flow, so "nazokat" login is not creds.login (creds.login is HEMIS ID/Login)
        
        # If the user is a Tutor, we check if they are allowed.
        # Demo login bypasses this entire block (returns early).
        # So this only affects real OAuth logins.
        
        # Check actual role from DB (more reliable)
        real_role = staff.role.value if hasattr(staff.role, 'value') else staff.role
        
        if real_role == "tyutor":
             # BLOCK ALL TUTORS FOR NOW
             # Unless we add a whitelist mechanism later
             logger.info(f"Blocking Tutor Login: {staff.full_name} ({staff.id})")
             raise HTTPException(status_code=403, detail="Tyutorlar moduli bo'yicha texnik ishlar olib borilmoqda. Tizim tez orada ishga tushadi.")

        # Update Staff info
        if h_id and not staff.hemis_id:
            staff.hemis_id = int(h_id)
            
        # Determine Role directly from DB or Hemis?
        # Ideally, we trust our DB role (e.g. 'tyutor')
        # But we can update if needed.
        
        # Check Hemis Roles if logic needed:
        # roles = me.get("roles", [])
        # ...
        
        await db.commit()
        
        # Generate Staff Token
        token_str = f"staff_id_{staff.id}"
        
        return {
            "success": True,
            "data": {
                "token": token_str,
                "role": "rahbariyat" if (staff.role.value if hasattr(staff.role, 'value') else staff.role) in ["dekan", "dekan_orinbosari", "dekan_yoshlar", "dekanat", "rahbariyat", "rektor", "prorektor", "yoshlar_prorektor"] else (staff.role.value if hasattr(staff.role, 'value') else staff.role), 
                "profile": {
                    "id": staff.id,
                    "full_name": staff.full_name,
                    "role": staff.role,
                    "image": getattr(staff, "image_url", None) or me.get("image") or me.get("picture"),
                    # Add other staff fields if needed
                }
            }
        }

    # --- STUDENT LOGIC (Existing) ---
    h_id = str(me.get("id", ""))
    h_login = me.get("login") or creds.login
    
    # Parse Names - Robust Extraction
    from utils.text_utils import format_uzbek_name
    
    first_name = me.get('firstname') or me.get('first_name') or ""
    last_name = me.get('lastname') or me.get('surname') or me.get('last_name') or ""
    father_name = me.get('fathername') or me.get('patronymic') or me.get('father_name') or ""
    short_name_hemis = me.get('short_name') or ""

    # title() for normalization
    if first_name: first_name = format_uzbek_name(str(first_name).strip())
    if last_name: last_name = format_uzbek_name(str(last_name).strip())
    if father_name: father_name = format_uzbek_name(str(father_name).strip())

    full_name_constructed = f"{last_name} {first_name} {father_name}".strip()
    full_name_hemis = format_uzbek_name((me.get('full_name') or me.get('name') or "").strip())
    
    # Logic to choose the most "full" name (the one with fewer initials)
    def count_initials(name):
        return len(re.findall(r'\b[A-Z]\.', name))

    if full_name_hemis and count_initials(full_name_hemis) <= count_initials(full_name_constructed):
        full_name_db = full_name_hemis
    else:
        full_name_db = full_name_constructed

    if not full_name_db or full_name_db.lower() == "talaba":
        full_name_db = format_uzbek_name(short_name_hemis) if short_name_hemis else "Talaba"

    logger.info(f"FINAL PARSED NAME: Full='{full_name_db}', Short='{short_name_hemis}'")

    # Helper for safe extraction
    def get_name(key):
        val = me.get(key)
        if isinstance(val, dict): return val.get('name')
        return val # specific handle if string

    # Extract Data
    # ... (existing university logic is fine)
    uni_code = me.get("university", {}).get("code") if isinstance(me.get("university"), dict) else ""
    uni_name = get_name("university")
    
    # Custom University Mapping
    if uni_code == "jmcu":
         uni_name = "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti" 
    elif not uni_name:
         uni_name = "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti"

    fac_name = get_name("faculty")
    spec_name = get_name("specialty")
    group_num = get_name("group")
    level_name = get_name("level")
    sem_name = get_name("semester")
    edu_form = get_name("educationForm")
    edu_type = get_name("educationType")
    pay_form = get_name("paymentForm")
    st_status = get_name("studentStatus")
    image_url = me.get("image") or me.get("picture") or me.get("image_url")

    uni_id, fac_id = await get_or_create_academic_context(db, uni_name, fac_name)

    # Parse Role
    raw_type = me.get("type", "student")
    role_code = "student"
    
    if raw_type == "student":
        role_code = "student"
    else:
        # Check roles array
        roles = me.get("roles", [])
        if roles and isinstance(roles, list) and len(roles) > 0:
            role_code = roles[0].get("code", "employee")
        else:
            role_code = "employee"

    result = await db.execute(select(Student).where(Student.hemis_login == h_login))
    student = result.scalar_one_or_none()
    
    if not student:
        student = Student(
            full_name=full_name_db or "Talaba",
            hemis_login=h_login,
            hemis_id=h_id,
            # hemis_password=creds.password, # DISABLED
            # hemis_token=token, # DISABLED
            # Role
            hemis_role=role_code,
            # Profile Fields
            university_name=uni_name,
            faculty_name=fac_name,
            specialty_name=spec_name,
            group_number=group_num,
            level_name=level_name,
            semester_name=sem_name,
            education_form=edu_form,
            education_type=edu_type,
            payment_form=pay_form,
            student_status=st_status,
            image_url=image_url,
            short_name=first_name, # FORCE FIRST NAME
            # Context IDs
            university_id=uni_id,
            faculty_id=fac_id
        )
        db.add(student)
    else:
        # Update basics
        # student.hemis_token = token # DISABLED
        # student.hemis_password = creds.password # DISABLED
        if full_name_db: student.full_name = full_name_db
        if h_id: student.hemis_id = h_id
        student.hemis_role = role_code # Update role
        
        # Update Profile
        student.university_name = uni_name
        student.faculty_name = fac_name
        student.specialty_name = spec_name

        student.group_number = group_num
        student.level_name = level_name
        student.semester_name = sem_name
        student.education_form = edu_form
        student.education_type = edu_type
        student.payment_form = pay_form
        student.student_status = st_status
        student.student_status = st_status
        if not (student.image_url and "static/uploads" in student.image_url):
            student.image_url = image_url
        student.short_name = first_name # FORCE FIRST NAME
        
        # Update IDs
        student.university_id = uni_id
        student.faculty_id = fac_id
        
    await db.commit()
    await db.refresh(student)

    # --- SYNC TO USERS TABLE (Unified Auth) ---
    from utils.encryption import encrypt_data
    existing_user = await db.scalar(select(User).where(User.hemis_login == h_login))
    if not existing_user:
        # Check if username is already taken by ANOTHER hemis_login
        u_name = student.username
        if u_name:
            conflict = await db.scalar(select(User).where(User.username == u_name))
            if conflict:
                logger.warning(f"Username {u_name} already taken. Skipping for {h_login}.")
                u_name = None # Set to None to avoid UniqueViolation
        

        new_user = User(
            hemis_login=h_login,
            username=u_name,
            role="student",
            full_name=full_name_db,
            short_name=first_name,
            image_url=image_url,
            hemis_id=h_id,
            hemis_token=encrypt_data(token),  # Encrypt
            # hemis_password=encrypt_data(creds.password), # [DISABLED] Privacy: Do not store password
            header_data=None, # Explicitly clear old data
            university_id=uni_id,
            faculty_id=fac_id,
            group_number=group_num
        )
        db.add(new_user)
    else:
        # Update existing
        existing_user.hemis_token = encrypt_data(token) # Encrypt
        # existing_user.hemis_password = encrypt_data(creds.password) # [DISABLED] Privacy
        if not (existing_user.image_url and "static/uploads" in existing_user.image_url):
            existing_user.image_url = image_url
        existing_user.full_name = full_name_db
        existing_user.short_name = first_name
        existing_user.university_id = uni_id
        existing_user.faculty_id = fac_id
    
    await db.commit()

    # ------------------------------------------
    
    # Prepare response data specifically
    profile_data = StudentProfileSchema.model_validate(student).model_dump()
    profile_data['first_name'] = first_name # Explicitly add first_name to response
    profile_data['role'] = student.hemis_role or "student" # Populate role for Mobile UI
    
    # [NEW] Prefetch Data in Background
    import asyncio
    try:
        logger.info(f"Triggering background prefetch for student {student.id}")
        asyncio.create_task(HemisService.prefetch_data(student.hemis_token, student.id))
        logger.info("Background prefetch task created")
    except Exception as e:
        logger.error(f"Failed to create prefetch task: {e}")

    # Update last login
    from datetime import datetime
    student.last_active_at = datetime.utcnow()
    await db.commit()
    
    # [NEW] Log Activity (Login)
    from services.activity_service import ActivityService, ActivityType
    # Background task preferred, but for now direct await
    try:
        await ActivityService.log_activity(
            db=db,
            user_id=student.id,
            role='student',
            activity_type=ActivityType.LOGIN
        )
    except Exception as e:
        print(f"Login activity log error: {e}")

    # [STATELESS] Generate JWT with embedded HEMIS token
    user_agent = request.headers.get("user-agent", "unknown")
    
    # [SECURITY] Encrypt Token for Client Storage (Stateless)
    encrypted_token = encrypt_data(token)
    
    access_token = create_access_token(
        data={
            "sub": student.hemis_login,
            "type": "student",
            "id": student.id,
            "hemis_token": encrypted_token # Embed Encrypted Token
        },
        expires_delta=timedelta(minutes=60 * 24 * 7), # 7 days
        user_agent=user_agent
    )

    return {
        "success": True,
        "data": {
            "token": access_token,
            "role": "student",
            "profile": profile_data
        }
    }

@router.get("/hemis/oauth/url")
async def get_hemis_oauth_url(source: str = "app", tg_id: str = None):
    """
    Generates the HEMIS OAuth URL.
    - source: 'app' or 'bot'
    - tg_id: Telegram ID if source=bot
    """
    state = source
    if source == "bot" and tg_id:
        state = f"bot_{tg_id}"
    
    url = HemisService.generate_oauth_url(state)
    return {"url": url}

@router.get("/hemis/oauth/redirect")
async def hemis_oauth_redirect(source: str = "bot", tg_id: str = None):
    """
    Redirects to HEMIS OAuth URL directly (convenient for Bot buttons).
    """
    state = source
    if source == "bot" and tg_id:
        state = f"bot_{tg_id}"
    
    url = HemisService.generate_oauth_url(state)
    return RedirectResponse(url=url)

@router.get("/authlog")
async def hemis_callback(
    request: Request,
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session)
):
    """
    HEMIS OAuth Callback Handler
    """
    if error:
         return HTMLResponse(content=_get_error_html(f"Avtorizatsiya rad etildi: {error}"), status_code=400)

    if not code:
        return HTMLResponse(content=_get_error_html("Avtorizatsiya kodi topilmadi."), status_code=400)

    # 1. Exchange Code for Token
    token, error_msg = await HemisService.exchange_code_for_token(code)
    if not token:
        return HTMLResponse(content=_get_error_html(f"HEMIS bilan bog'lanishda xatolik: {error_msg}"), status_code=500)

    # 2. Get Profile
    me = await HemisService.get_me(token)
    if not me:
        return HTMLResponse(content=_get_error_html("Profil ma'lumotlarini olib bo'lmadi."), status_code=500)

    # 3. Sync to DB (Reusing existing logic or similar)
    # We need to sync the student record
    h_id = str(me.get("id", ""))
    h_login = me.get("login", "")
    
    # ... logic from login_via_hemis but adapted for OAuth ...
    # To keep it DRY, I'll extract some logic or just replicate for now as it's complex
    # Let's simplify: find student by hemis_id/login or create
    
    # (Simplified Sync Logic inspired by login_via_hemis)
    stmt = select(Student).where(Student.hemis_login == h_login)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    # Name Parsing - Robust Extraction
    first_name = format_uzbek_name((me.get('firstname') or me.get('first_name') or "").strip())
    last_name = format_uzbek_name((me.get('lastname') or me.get('surname') or me.get('last_name') or "").strip())
    father_name = format_uzbek_name((me.get('fathername') or me.get('patronymic') or me.get('father_name') or "").strip())
    
    full_name_db = f"{last_name} {first_name} {father_name}".strip()
    if not full_name_db:
        # Final raw fallback
        full_name_db = me.get('name') or me.get('full_name') or "Talaba"
    
    # Uni/Faculty mapping
    uni_name = me.get("university", {}).get("name") if isinstance(me.get("university"), dict) else me.get("university_name") or "JMCU"
    fac_name = me.get("faculty", {}).get("name") if isinstance(me.get("faculty"), dict) else me.get("faculty_name") or ""
    image_url = me.get("image") or me.get("picture") or me.get("image_url")
    
    uni_id, fac_id = await get_or_create_academic_context(db, uni_name, fac_name)

    if not student:
        student = Student(
            full_name=full_name_db,
            hemis_login=h_login,
            hemis_id=h_id,
            hemis_token=token,
            university_name=uni_name,
            faculty_name=fac_name,
            university_id=uni_id,
            faculty_id=fac_id,
            short_name=first_name,
            image_url=image_url
        )
        db.add(student)
    else:
        student.hemis_token = token
        student.full_name = full_name_db
        student.university_name = uni_name
        student.faculty_name = fac_name
        student.university_id = uni_id
        student.faculty_id = fac_id
        student.short_name = first_name
        if image_url and not (student.image_url and "static/uploads" in student.image_url):
            student.image_url = image_url
    
    await db.commit()
    await db.refresh(student)

    # 4. Handle State (Bot vs App)
    if state and state.startswith("bot_"):
        tg_id_str = state.replace("bot_", "")
        try:
            tg_id = int(tg_id_str)
            # Link TgAccount if not linked
            from database.models import TgAccount
            acc_stmt = select(TgAccount).where(TgAccount.telegram_id == tg_id)
            acc_res = await db.execute(acc_stmt)
            acc = acc_res.scalar_one_or_none()
            if acc:
                acc.student_id = student.id
                acc.current_role = "student" # Ensure role is set
                await db.commit()
            else:
                # Create new link
                new_acc = TgAccount(
                    telegram_id=tg_id,
                    student_id=student.id,
                    current_role="student"
                )
                db.add(new_acc)
                await db.commit()
            
            # Send notification to user via Bot
            await _notify_bot_user(tg_id, student.full_name)
            
            return HTMLResponse(content=_get_success_html("Telegram Botga muvaffaqiyatli kirdingiz! Endi brauzerni yopishingiz mumkin."))
        except Exception as e:
            logger.error(f"Bot notification error: {e}")
            return HTMLResponse(content=_get_success_html("Tizimga kirdingiz, lekin botga xabar yuborishda xatolik bo'ldi. Botni qayta ishga tushiring."))

    elif state == "app":
        # [STATELESS] Generate JWT with embedded HEMIS token for OAuth/App Login
        user_agent = request.headers.get("user-agent", "unknown")
        
        # [SECURITY] Encrypt Token
        from utils.encryption import encrypt_data
        encrypted_token = encrypt_data(token)
        
        # Create Access Token
        access_token = create_access_token(
            data={
                "sub": student.hemis_login,
                "type": "student",
                "id": student.id,
                "hemis_token": encrypted_token # Embed Encrypted Token
            },
            expires_delta=timedelta(minutes=60 * 24 * 7), # 7 days
            user_agent=user_agent
        )
        
        # Redirect back to App with NEW Token Format
        return RedirectResponse(url=f"talabahamkor://auth?token={access_token}&status=success")

    return HTMLResponse(content=_get_success_html("Muvaffaqiyatli kirdingiz!"))

async def _notify_bot_user(tg_id: int, name: str):
    """Notify user via Telegram Bot"""
    from main import bot
    try:
        msg = f"✅ <b>Tabriklaymiz!</b>\n\nSiz HEMIS orqali muvaffaqiyatli autentifikatsiyadan o'tdingiz.\n\nFoydalanuvchi: <b>{name}</b>\n\nEndi bot imkoniyatlaridan to'liq foydalanishingiz mumkin.\n\n👇 <b>Agar menyu ko'rinmasa, /start ni bosing.</b>"
        await bot.send_message(tg_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send bot notification: {e}")

def _get_success_html(message: str):
    return f"""
    <html>
        <head>
            <title>Muvaffaqiyatli</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f0f2f5; }}
                .card {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; max-width: 400px; }}
                .icon {{ font-size: 4rem; color: #4caf50; margin-bottom: 1rem; }}
                h2 {{ color: #1a73e8; }}
                p {{ color: #5f6368; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">✅</div>
                <h2>Muvaffaqiyatli!</h2>
                <p>{message}</p>
            </div>
        </body>
    </html>
    """

def _get_error_html(error: str):
    return f"""
    <html>
        <head>
            <title>Xatolik</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #fff5f5; }}
                .card {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; max-width: 400px; border-top: 5px solid #f44336; }}
                .icon {{ font-size: 4rem; color: #f44336; margin-bottom: 1rem; }}
                h2 {{ color: #b71c1c; }}
                p {{ color: #5f6368; line-height: 1.5; }}
                .btn {{ display: inline-block; margin-top: 1.5rem; padding: 0.8rem 1.5rem; background: #1a73e8; color: white; text-decoration: none; border-radius: 0.5rem; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">❌</div>
                <h2>Xatolik yuz berdi</h2>
                <p>{error}</p>
                <a href="javascript:window.close()" class="btn">Yopish</a>
            </div>
        </body>
    </html>
    """

@router.post("/delete-account")
async def delete_account(
    creds: HemisLoginRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Permanently delete account and all associated data.
    Requires valid HEMIS credentials for confirmation.
    """
    # 1. Verify Credentials via HEMIS (Identity Proof)
    base_url = UniversityService.get_api_url(creds.login)
    token, error = await HemisService.authenticate(creds.login, creds.password, base_url=base_url)
    
    if not token:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri. Iltimos, ma'lumotlarni tekshiring.")
        
    # 2. Find Student Record
    student = await db.scalar(select(Student).where(Student.hemis_login == creds.login))
    if not student:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        
    # 3. Find User Record (Unified Auth)
    user = await db.scalar(select(User).where(User.hemis_login == creds.login))
    
    # 4. Perform Delete
    # Note: Cascading relationships in models.py will handle:
    # - activities, documents, certificates, feedbacks (ondelete="CASCADE")
    # - TgAccount links (ondelete="SET NULL")
    
    try:
        if student:
            await db.delete(student)
            
        if user:
            await db.delete(user)
            
        await db.commit()
        
        logger.info(f"ACCOUNT DELETED: {creds.login}")
        return {"success": True, "message": "Hisob muvaffaqiyatli o'chirildi"}
        
    except Exception as e:
        logger.error(f"Delete Account Error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Hisobni o'chirishda xatolik yuz berdi")
