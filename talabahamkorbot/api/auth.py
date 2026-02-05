from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db_connect import get_session
from database.models import Student, User
from services.hemis_service import HemisService
from api.schemas import HemisLoginRequest, StudentProfileSchema
import logging

from api.schemas import HemisLoginRequest, StudentProfileSchema
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def _get_or_create_academic_context(db: AsyncSession, uni_name: str, fac_name: str = None):
    """Maps names to IDs, creating records if they don't exist."""
    from database.models import University, Faculty
    if not uni_name:
        return None, None
        
    # 1. University
    uni = await db.scalar(select(University).where(University.name == uni_name))
    if not uni:
        # Check for similar names or use a default code
        uni_code = uni_name.replace(" ", "_").upper()[:32]
        uni = University(name=uni_name, uni_code=uni_code)
        db.add(uni)
        await db.flush()
        logger.info(f"Created new University: {uni_name}")
    
    uni_id = uni.id
    fac_id = None
    
    # 2. Faculty
    if fac_name:
        fac = await db.scalar(select(Faculty).where(Faculty.university_id == uni_id, Faculty.name == fac_name))
        if not fac:
            fac_code = "AUTO_" + fac_name.replace(" ", "_")[:59]
            fac = Faculty(university_id=uni_id, faculty_code=fac_code, name=fac_name)
            db.add(fac)
            await db.flush()
            logger.info(f"Created new Faculty: {fac_name} for University {uni_id}")
        fac_id = fac.id
        
    return uni_id, fac_id

@router.post("/hemis")
@router.post("/hemis/")
async def login_via_hemis(
    creds: HemisLoginRequest,
    db: AsyncSession = Depends(get_session)
):
    # 1. AUTHENTICATE
    import os
    login_clean = creds.login.strip().lower()
    pass_clean = creds.password.strip()
    
    print(f"DEBUG AUTH: login='{login_clean}', pass='{pass_clean}'")
    
    if pass_clean == "123":
         demo_login = None
         full_name = ""
         role = ""
         
         if login_clean == "demo":
             demo_login = "demo.student"
             full_name = "Demo Talaba"
             role = "student"
         elif login_clean == "tyutor":
             demo_login = "demo.tutor"
             full_name = "Demo Tyutor"
             role = "tutor"
         elif login_clean == "tyutor_demo":
             demo_login = "demo.tutor_new"
             full_name = "Yangi Demo Tyutor"
             role = "tutor"
             
         print(f"DEBUG AUTH: demo_login='{demo_login}'")
             
         if demo_login:
             if role == "tutor":
                 # Demo Staff Logic
                 from database.models import Staff, StaffRole
                 demo_staff = await db.scalar(select(Staff).where(Staff.hemis_id == 999999))
                 if not demo_staff:
                     demo_staff = Staff(
                         full_name=full_name,
                         jshshir="12345678901234",
                         role="tyutor", # or StaffRole.TUTOR
                         hemis_id=999999,
                         phone="998901234567"
                     )
                     db.add(demo_staff)
                     await db.commit()
                     await db.refresh(demo_staff)
                 
                 print(f"DEBUG AUTH: Success! Token='staff_id_{demo_staff.id}'")
                 return {
                     "success": True, 
                     "data": {
                         "token": f"staff_id_{demo_staff.id}",
                         "role": "tyutor",
                         "profile": {
                              "id": demo_staff.id,
                              "full_name": demo_staff.full_name,
                              "role": "tyutor",
                              "image": f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=random"
                         }
                     }
                 }
             else:
                 # Demo Student Logic
                 # Ensure Demo User Exists
                 demo_user = await db.scalar(select(Student).where(Student.hemis_login == demo_login))
                 if not demo_user:
                     demo_user = Student(
                         hemis_id=f"{login_clean}_123",
                         full_name=full_name,
                         hemis_login=demo_login,
                         hemis_password="123",
                         university_name="Test Universiteti",
                         faculty_name="Test Fakulteti",
                         level_name="1-kurs",
                         group_number="101-GROUP",
                         hemis_role=role,
                         image_url=f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=random"
                     )
                     db.add(demo_user)
                     await db.flush()
                     
                     # Also sync to Users table
                     new_u = User(
                         hemis_login=demo_login,
                         role=role,
                         full_name=full_name,
                         hemis_password="123",
                         university_name="Test Universiteti",
                         faculty_name="Test Fakulteti"
                     )
                     db.add(new_u)
                     await db.commit()
                     await db.refresh(demo_user)
                 
                 print(f"DEBUG AUTH: Success! Token='student_id_{demo_user.id}'")
                 
                 return {
                     "success": True,
                     "data": {
                         "token": f"student_id_{demo_user.id}",
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
    t_start = time.time()
    token, error = await HemisService.authenticate(creds.login, creds.password)
    t_auth = time.time()
    print(f"AuthLog: Authenticate took {t_auth - t_start:.2f}s", flush=True)
    
    if not token:
        logger.warning(f"AuthLog: Auth failed via Hemis: {error}")
        raise HTTPException(status_code=401, detail=error or "Login yoki parol noto'g'ri")
        

    # 2. GET PROFILE
    print(f"AuthLog: Fetching profile for login {creds.login}...", flush=True)
    me = await HemisService.get_me(token)
    t_profile = time.time()
    print(f"AuthLog: Get Me took {t_profile - t_auth:.2f}s", flush=True)
    
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
                "role": staff.role.value if hasattr(staff.role, 'value') else staff.role, # e.g. "tyutor"
                "profile": {
                    "id": staff.id,
                    "full_name": staff.full_name,
                    "role": staff.role,
                    "image": me.get("image") or me.get("picture"),
                    # Add other staff fields if needed
                }
            }
        }

    # --- STUDENT LOGIC (Existing) ---
    h_id = str(me.get("id", ""))
    h_login = me.get("login") or creds.login
    
    # Parse Names - Robust Extraction
    first_name = me.get('firstname') or me.get('first_name') or ""
    last_name = me.get('lastname') or me.get('surname') or me.get('last_name') or ""
    father_name = me.get('fathername') or me.get('patronymic') or me.get('father_name') or ""
    short_name_hemis = me.get('short_name') or ""

    # title() for normalization
    if first_name: first_name = str(first_name).strip().title()
    if last_name: last_name = str(last_name).strip().title()
    if father_name: father_name = str(father_name).strip().title()

    full_name_db = f"{last_name} {first_name} {father_name}".strip()

    # Fallback to 'name' or existing full_name if individual fields missing
    if not first_name or not last_name:
        raw_name = me.get('name') or me.get('full_name') or ""
        if raw_name:
            full_name_db = " ".join(raw_name.split()).title()
        
    if not full_name_db or full_name_db.lower() == "talaba":
        if short_name_hemis:
            full_name_db = short_name_hemis.title()
        else:
            full_name_db = "Talaba"

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
    if uni_code == "jmcu" or "pedagogika" in (uni_name or "").lower():
         uni_name = "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti" 
    elif not uni_name:
         uni_name = "JMCU"

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

    # Mapping Names -> IDs for Community Filtering
    uni_id, fac_id = await _get_or_create_academic_context(db, uni_name, fac_name)

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
            hemis_password=creds.password,
            hemis_token=token,
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
            short_name=short_name_hemis or first_name,
            # Context IDs
            university_id=uni_id,
            faculty_id=fac_id
        )
        db.add(student)
    else:
        # Update basics
        student.hemis_token = token
        student.hemis_password = creds.password 
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
        student.short_name = short_name_hemis or first_name
        
        # Update IDs
        student.university_id = uni_id
        student.faculty_id = fac_id
        
    await db.commit()
    await db.refresh(student)

    # --- SYNC TO USERS TABLE (Unified Auth) ---
    existing_user = await db.scalar(select(User).where(User.hemis_login == h_login))
    if not existing_user:
        new_user = User(
            hemis_login=h_login,
            username=student.username, # Should be None initially or synced if Student has it
            role="student", # Default for now, can improve with role_code
            full_name=full_name_db,
            short_name=first_name,
            image_url=image_url,
            # phone=me.get("phone"), # If available
            hemis_id=h_id,
            hemis_token=token,
            hemis_password=creds.password,
            
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
            university_id=uni_id,
            faculty_id=fac_id
        )
        db.add(new_user)
    else:
        # Update existing
        existing_user.hemis_token = token
        existing_user.hemis_password = creds.password
        existing_user.hemis_password = creds.password
        # Only overwrite image if it's NOT a custom upload
        if not (existing_user.image_url and "static/uploads" in existing_user.image_url):
            existing_user.image_url = image_url
        existing_user.full_name = full_name_db
        existing_user.short_name = first_name
        # Update academic info
        existing_user.group_number = group_num
        existing_user.level_name = level_name
        existing_user.semester_name = sem_name
        # Update IDs
        existing_user.university_id = uni_id
        existing_user.faculty_id = fac_id
        # ... other fields if needed
    
    await db.commit()
    # ------------------------------------------
    
    # Prepare response data specifically
    profile_data = StudentProfileSchema.model_validate(student).model_dump()
    profile_data['first_name'] = first_name # Explicitly add first_name to response
    profile_data['role'] = student.hemis_role or "student" # Populate role for Mobile UI
    
    return {
        "success": True,
        "data": {
            "token": f"student_id_{student.id}",
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
    first_name = (me.get('firstname') or me.get('first_name') or "").strip().title()
    last_name = (me.get('lastname') or me.get('surname') or me.get('last_name') or "").strip().title()
    father_name = (me.get('fathername') or me.get('patronymic') or me.get('father_name') or "").strip().title()
    
    full_name_db = f"{last_name} {first_name} {father_name}".strip()
    if not full_name_db:
        # Final raw fallback
        full_name_db = me.get('name') or me.get('full_name') or "Talaba"
    
    # Uni/Faculty mapping
    uni_name = me.get("university", {}).get("name") if isinstance(me.get("university"), dict) else me.get("university_name") or "JMCU"
    fac_name = me.get("faculty", {}).get("name") if isinstance(me.get("faculty"), dict) else me.get("faculty_name") or ""
    image_url = me.get("image") or me.get("picture") or me.get("image_url")
    
    # Map IDs
    uni_id, fac_id = await _get_or_create_academic_context(db, uni_name, fac_name)

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
        if image_url: student.image_url = image_url
    
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
        # Generate our internal token (session check)
        # Using the same format as login_via_hemis for now
        app_token = f"student_id_{student.id}"
        # Redirect back to App via Deep Link
        return RedirectResponse(url=f"talabahamkor://auth?token={app_token}&status=success")

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
    token, error = await HemisService.authenticate(creds.login, creds.password)
    
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
