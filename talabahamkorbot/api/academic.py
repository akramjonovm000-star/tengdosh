from fastapi_cache.decorator import cache
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.hemis_service import HemisService
from database.db_connect import get_session
from api.dependencies import get_current_student
from database.models import Student, TgAccount

router = APIRouter()

@router.get("/grades")
@cache(expire=600)
async def get_grades(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
         return {"success": False, "message": "No Token", "data": []}

    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    # 1. Determine Semester Code
    sem_code = semester
    if not sem_code:
        # 1.1 Try Semester List first (Most accurate)
        semesters = await HemisService.get_semester_list(student.hemis_token)
        if semesters:
            latest = semesters[0]
            sem_code = str(latest.get("code") or latest.get("id"))
        else:
            # 1.2 Fallback to Profile
            me_data = await HemisService.get_me(student.hemis_token)
            if me_data:
                sem = me_data.get("semester", {})
                if not sem: sem = me_data.get("currentSemester", {})
                if sem and isinstance(sem, dict):
                     sem_code = str(sem.get("code") or sem.get("id"))

    # 2. Get Subjects (Grades are embedded in subject list)
    subjects_data = await HemisService.get_student_subject_list(
        student.hemis_token, 
        semester_code=sem_code, 
        student_id=student.id,
        force_refresh=refresh
    )

    results = []
    for item in (subjects_data or []):
        subject_info = item.get("curriculumSubject", {})
        sub_details = subject_info.get("subject", {})
        name = sub_details.get("name") or item.get("subject", {}).get("name", "Nomsiz fan")
        s_id = sub_details.get("id") or item.get("subject", {}).get("id")

        # Detailed Grades via HemisService helper
        detailed = HemisService.parse_grades_detailed(item)
        on = next((g for g in detailed if g['type'] == 'ON'), {"val_5": 0, "raw": 0})
        yn = next((g for g in detailed if g['type'] == 'YN'), {"val_5": 0, "raw": 0})
        jn = next((g for g in detailed if g['type'] == 'JN'), {"val_5": 0, "raw": 0})

        results.append({
            "id": s_id,
            "subject": name,
            "name": name,
            "overall_grade": item.get("overallScore", {}).get("grade", 0),
            "on": on,
            "yn": yn,
            "jn": jn,
            "detailed": detailed
        })

    return {"success": True, "data": results}

@router.get("/semesters")
@cache(expire=3600)
async def get_semesters(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}

    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    # Match Bot Logic: Calculate semesters from 11 (1-semestr) up to current
    me_data = await HemisService.get_me(student.hemis_token)
    current_sem_code = 11
    if me_data:
        sem = me_data.get("semester", {})
        if not sem: sem = me_data.get("currentSemester", {})
        if sem and isinstance(sem, dict):
            try:
                current_sem_code = int(sem.get("code") or 11)
            except: pass
            
    if current_sem_code < 11: current_sem_code = 11
    
    results = []
    # range(11, 12) gives only [11], excluding 12 (which is 'Joriy')
    for code in range(11, current_sem_code):
        sem_num = code - 10
        results.append({
            "code": str(code),
            "id": str(code),
            "name": f"{sem_num}-semestr"
        })
    
    # Sort descending so latest history is first
    results.reverse()
    
    return {"success": True, "data": results}

@router.get("/schedule")
@cache(expire=3600)  # Cache for 1 hour
async def get_schedule(
    semester: str = None,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}

    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    # 1. Determine Semester Code
    sem_code = semester
    if not sem_code:
        semesters = await HemisService.get_semester_list(student.hemis_token)
        if semesters:
            latest = semesters[0]
            sem_code = str(latest.get("code") or latest.get("id"))
        else:
            me_data = await HemisService.get_me(student.hemis_token)
            if me_data:
                sem = me_data.get("semester", {})
                if not sem: sem = me_data.get("currentSemester", {})
                if sem and isinstance(sem, dict):
                     sem_code = str(sem.get("code") or sem.get("id"))

    # 2. Fetch Schedule
    schedule_data = await HemisService.get_student_schedule_cached(
        student.hemis_token, 
        semester_code=sem_code, 
        student_id=student.id
    )

    if not schedule_data:
        return {"success": True, "data": []}

    # 3. Enrich Topics from Curriculum
    # Group lessons by (subject_id, training_type_code) to find their order
    lessons_by_group = {}
    for item in schedule_data:
        s_id = str(item.get("subject", {}).get("id") or "")
        t_type = str(item.get("trainingType", {}).get("code") or "")
        
        if not s_id: continue
        key = (s_id, t_type)
        if key not in lessons_by_group:
            lessons_by_group[key] = []
        lessons_by_group[key].append(item)

    # Sort each group by date/time
    for key, group in lessons_by_group.items():
        # HEMIS timestamps 'lesson_date' are in seconds
        group.sort(key=lambda x: (int(x.get("lesson_date") or 0), x.get("start_time") or ""))

    # Fetch curriculum topics for each subject
    unique_subjects = set(k[0] for k in lessons_by_group.keys())
    for s_id in unique_subjects:
        # We process each training type separately
        for t_code in set(k[1] for k in lessons_by_group.keys() if k[0] == s_id):
            topics = await HemisService.get_curriculum_topics(
                student.hemis_token, 
                subject_id=s_id, 
                semester_code=sem_code, 
                training_type_code=t_code,
                student_id=student.id
            )
            
            if topics:
                # Map N-th lesson in schedule to N-th topic in curriculum
                group = lessons_by_group[(s_id, t_code)]
                for idx, lesson_item in enumerate(group):
                    # Only override if lesson_topic is missing/default
                    current_topic = lesson_item.get("lesson_topic") or lesson_item.get("theme") or ""
                    if not current_topic or current_topic == "Mavzu kiritilmagan":
                        if idx < len(topics):
                            # The 'name' field in /v1/data/curriculum-subject-topic-list holds the topic title
                            lesson_item["lesson_topic"] = topics[idx].get("name") or lesson_item.get("lesson_topic")

    return {"success": True, "data": schedule_data}

@router.get("/subjects")
@cache(expire=600)
async def get_subjects(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}

    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    import asyncio
    
    # 1. Determine Semester Code
    sem_code = semester
    if not sem_code:
        semesters = await HemisService.get_semester_list(student.hemis_token)
        if semesters:
            latest = semesters[0]
            sem_code = str(latest.get("code") or latest.get("id"))
        else:
            me_data = await HemisService.get_me(student.hemis_token)
            if me_data:
                sem = me_data.get("semester", {})
                if not sem: sem = me_data.get("currentSemester", {})
                if sem and isinstance(sem, dict):
                     sem_code = str(sem.get("code") or sem.get("id"))
    
    # 2. Fetch data concurrently
    subjects_task = HemisService.get_student_subject_list(student.hemis_token, semester_code=sem_code, student_id=student.id, force_refresh=refresh)
    absence_task = HemisService.get_student_absence(student.hemis_token, semester_code=sem_code, student_id=student.id, force_refresh=refresh)
    schedule_task = HemisService.get_student_schedule_cached(student.hemis_token, semester_code=sem_code, student_id=student.id, force_refresh=refresh)
    
    subjects_data, attendance_result, schedule_data = await asyncio.gather(
        subjects_task, absence_task, schedule_task
    )
    
    # ... rest of processing ...
    abs_map = {}
    if isinstance(attendance_result, (tuple, list)) and len(attendance_result) >= 4:
        att_items = attendance_result[3]
        for item in att_items:
            s_name = item.get("subject", {}).get("name")
            if s_name:
                s_name_lower = s_name.lower().strip()
                abs_map[s_name_lower] = abs_map.get(s_name_lower, 0) + item.get("hour", 2)

    teacher_map = {}
    if schedule_data:
        for item in schedule_data:
            s_name = item.get("subject", {}).get("name")
            if not s_name: continue
            s_name_lower = s_name.lower().strip()
            t_name = item.get("employee", {}).get("name")
            if not t_name: continue
            train_type = item.get("trainingType", {}).get("name", "Boshqa")
            if s_name_lower not in teacher_map:
                teacher_map[s_name_lower] = {"lecturer": None, "seminar": None}
            if "ma'ruza" in train_type.lower() or "lecture" in train_type.lower():
                teacher_map[s_name_lower]["lecturer"] = t_name
            else:
                teacher_map[s_name_lower]["seminar"] = t_name

    results = []
    for item in (subjects_data or []):
        subject_info = item.get("curriculumSubject", {})
        sub_details = subject_info.get("subject", {})
        name = sub_details.get("name", "Nomsiz fan")
        s_id = sub_details.get("id")
        name_lower = name.lower().strip()
        t_info = teacher_map.get(name_lower, {})
        detailed = HemisService.parse_grades_detailed(item)
        on = next((g for g in detailed if g['type'] == 'ON'), {"val_5": 0, "raw": 0})
        yn = next((g for g in detailed if g['type'] == 'YN'), {"val_5": 0, "raw": 0})
        jn = next((g for g in detailed if g['type'] == 'JN'), {"val_5": 0, "raw": 0})
        
        results.append({
            "id": s_id,
            "name": name,
            "lecturer": t_info.get("lecturer"),
            "seminar": t_info.get("seminar"),
            "absent_hours": abs_map.get(name_lower, 0),
            "overall_grade": item.get("overallScore", {}).get("grade", 0),
            "grades": {
                "ON": on, "YN": yn, "JN": jn, "detailed": detailed
            }
        })
        
    return {"success": True, "data": results}

@router.get("/resources/{subject_id}")
async def get_resources(
    subject_id: str,
    student: Student = Depends(get_current_student)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}
        
    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    resources = await HemisService.get_student_resources(student.hemis_token, subject_id=subject_id)
    
    parsed = []
    for res in resources:
        topics = []
        for item in res.get("subjectFileResourceItems", []):
            for f in item.get("files", []):
                topics.append({
                    "id": item.get("id"),
                    "name": f.get("name") or "Fayl",
                    "url": f.get("url")
                })
        parsed.append({
            "id": res.get("id"),
            "title": res.get("title") or "Mavzu",
            "files": topics
        })
    return {"success": True, "data": parsed}

@router.get("/attendance")
@cache(expire=300)
async def get_attendance(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}

    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    sem_code = semester
    if not sem_code:
        # Resolve latest semester dynamically
        semesters = await HemisService.get_semester_list(student.hemis_token)
        if semesters:
            # get_semester_list is already sorted descending by code
            latest = semesters[0]
            sem_code = str(latest.get("code") or latest.get("id"))
        else:
            # Fallback to profile if list fails
            me_data = await HemisService.get_me(student.hemis_token)
            if me_data:
                sem = me_data.get("semester", {})
                if not sem: sem = me_data.get("currentSemester", {}) # Multi-key fallback
                if sem and isinstance(sem, dict):
                     sem_code = str(sem.get("code") or sem.get("id"))
    
    # Use force_refresh parameter in HemisService call
    _, _, _, data = await HemisService.get_student_absence(
        student.hemis_token, 
        semester_code=sem_code, 
        student_id=student.id,
        force_refresh=refresh
    )
    
    if not semester and not data:
        me_data = await HemisService.get_me(student.hemis_token)
        if me_data:
            curr_sem = me_data.get("currentSemester", {})
            if curr_sem:
                current_sem_code = str(curr_sem.get("code", "12"))
                try:
                    prev_code = str(int(current_sem_code) - 1)
                    _, _, _, data_prev = await HemisService.get_student_absence(student.hemis_token, semester_code=prev_code, student_id=student.id)
                    if data_prev: data = data_prev
                except: pass

    parsed = []
    for item in data:
        subj_name = item.get("subject", {}).get("name", "Fan")
        ts = item.get("lesson_date")
        date_str = item.get("date", "") 
        if ts and not date_str:
            from datetime import datetime
            try: date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except: pass
        lesson_theme = item.get("trainingType", {}).get("name", "")
        absent_on = item.get("absent_on", 0)
        absent_off = item.get("absent_off", 0)
        hours = absent_on + absent_off
        if hours == 0: hours = item.get("hour", 2)
        is_excused = item.get("explicable", False)
        if absent_on > 0 and absent_off == 0: is_excused = True
        elif absent_off > 0 and absent_on == 0: is_excused = False
            
        parsed.append({
            "subject": subj_name, "date": date_str, "theme": lesson_theme,
            "hours": hours, "is_excused": is_excused
        })

    total_hours = sum(p['hours'] for p in parsed)
    excused_hours = sum(p['hours'] for p in parsed if p['is_excused'])
    unexcused_hours = total_hours - excused_hours
    
    return {
        "success": True, 
        "data": {
            "total": total_hours, "excused": excused_hours,
            "unexcused": unexcused_hours, "items": parsed
        }
    }

from pydantic import BaseModel
class ResourceSendRequest(BaseModel):
    url: str
    name: str

@router.post("/resources/send")
async def send_resource_to_bot(
    req: ResourceSendRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}
        
    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalar_one_or_none()
    if not tg_account:
        return {"success": False, "message": "Telegram hisob ulanmagan."}
    
    content, filename = await HemisService.download_resource_file(student.hemis_token, req.url)
    if not content:
         return {"success": False, "message": "Failed to download file."}
         
    try:
        from bot import bot
        from aiogram.types import BufferedInputFile
        final_name = filename if filename and "document" not in filename else req.name
        if "." not in final_name: final_name += ".pdf"
        input_file = BufferedInputFile(content, filename=final_name)
        await bot.send_document(chat_id=tg_account.telegram_id, document=input_file, caption=f"📄 {req.name}")
        return {"success": True, "message": "Sent!"}
    except Exception as e:
        return {"success": False, "message": f"Bot Error: {str(e)}"}

@router.get("/subject/{subject_id}/details")
async def get_subject_details_endpoint(
    subject_id: str,
    semester: str = None,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if not student.hemis_token:
        return {"success": False, "message": "No Token"}
        
    # 0. Check Auth Status
    if await HemisService.check_auth_status(student.hemis_token) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    subjects = await HemisService.get_student_subject_list(student.hemis_token, semester_code=semester)
    
    def get_nested(d, path):
        keys = path.split(".")
        val = d
        for k in keys:
             if isinstance(val, dict): val = val.get(k, {})
             else: return None
        return val if val != {} else None

    target_subject = next((s for s in subjects if str(get_nested(s, "curriculumSubject.subject.id") or get_nested(s, "subject.id")) == str(subject_id)), None)
                  
    subject_info = {}
    if target_subject:
        curr_subj = target_subject.get("curriculumSubject", {})
        detailed = HemisService.parse_grades_detailed(target_subject)
        subject_info = {
            "name": get_nested(curr_subj, "subject.name") or get_nested(target_subject, "subject.name"),
            "total_hours": curr_subj.get("total_acload", 0),
            "grades": {
                "overall": target_subject.get("overallScore", {}).get("grade", 0),
                "detailed": detailed
            }
        }
    else: subject_info = {"name": "Fan topilmadi", "total_hours": 0, "grades": {"overall": 0}}

    schedule = await HemisService.get_student_schedule_cached(student.hemis_token, semester_code=semester, student_id=student.id)
    teachers = set()
    if schedule:
        for item in schedule:
            if str(get_nested(item, "subject.id")) == str(subject_id):
                 t_name = get_nested(item, "employee.name")
                 if t_name: teachers.add(t_name)
    
    _, _, _, absence_items = await HemisService.get_student_absence(student.hemis_token, semester_code=semester, student_id=student.id)
    subject_absence = []
    total_missed = 0
    if absence_items:
        for item in absence_items:
             if str(get_nested(item, "subject.id")) == str(subject_id):
                 hours = item.get("absent_on", 0) + item.get("absent_off", 0)
                 if hours == 0: hours = item.get("hour", 2)
                 from datetime import datetime
                 date_str = datetime.fromtimestamp(item.get("lesson_date")).strftime("%d.%m.%Y") if item.get("lesson_date") else ""
                 subject_absence.append({"date": date_str, "hours": hours})
                 total_missed += hours

    return {
        "success": True, 
        "data": {
            "subject": subject_info, "teachers": list(teachers),
            "attendance": {"total_missed": total_missed, "details": subject_absence}
        }
    }
