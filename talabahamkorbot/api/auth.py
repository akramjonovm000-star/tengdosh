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

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/hemis")
@router.post("/hemis/")
async def login_via_hemis(
    creds: HemisLoginRequest,
    db: AsyncSession = Depends(get_session)
):
    # 1. AUTHENTICATE
    import os
    if creds.login == "demo" and creds.password == "123" and os.environ.get("TEST_MODE") == "true":
         # DEMO BACKDOOR (TEST MODE ONLY)
         # Ensure Demo User Exists
         demo_user = await db.scalar(select(Student).where(Student.hemis_login == "demo.student"))
         if not demo_user:
             demo_user = Student(
                 hemis_id="demo_123",
                 full_name="Demo Talaba",
                 hemis_login="demo.student",
                 hemis_password="123",
                 university_name="Test Universiteti",
                 faculty_name="Test Fakulteti",
                 level_name="1-kurs",
                 group_number="101-GROUP",
                 image_url="https://ui-avatars.com/api/?name=Demo+Talaba&background=random"
             )
             db.add(demo_user)
             await db.commit()
             await db.refresh(demo_user)
         
         # Create Token (Import safely)
         from handlers.auth import create_access_token 
         token = create_access_token(data={"sub": str(demo_user.id), "role": "student"})
         
         return {
             "success": True,
             "token": token,
             "role": "student",
             "data": {
                 "token": token,
                 "role": "student",
                 "profile": {
                     "id": demo_user.id,
                     "full_name": demo_user.full_name,
                     "university": {"name": demo_user.university_name},
                     "image": demo_user.image_url
                 }
             }
         }

    # 1. AUTHENTICATE
    import time
    t_start = time.time()
    print(f"AuthLog: Login attempt for {creds.login}...", flush=True)

    import os
    if creds.login == "demo" and creds.password == "123" and os.environ.get("TEST_MODE") == "true":
         # ...
         pass 

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
    
    # DEBUG LOGGING
    import json
    # logger.info(f"HEMIS RAW PROFILE REPSONSE: {json.dumps(me, indent=2)}") 
    # Reduced log spam
    
    if not me:
        raise HTTPException(status_code=500, detail="Profil ma'lumotlarini olib bo'lmadi")
        
    # 3. SYNC TO DB
    h_id = str(me.get("id", ""))
    h_login = me.get("login") or creds.login
    
    # Parse Names - Expanded Logic
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
            short_name=short_name_hemis or first_name
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
    
    if not student:
        student = Student(
            full_name=full_name_db,
            hemis_login=h_login,
            hemis_id=h_id,
            hemis_token=token,
            university_name=uni_name,
            faculty_name=fac_name,
            short_name=first_name,
            image_url=image_url
        )
        db.add(student)
    else:
        student.hemis_token = token
        student.full_name = full_name_db
        student.university_name = uni_name
        student.faculty_name = fac_name
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
