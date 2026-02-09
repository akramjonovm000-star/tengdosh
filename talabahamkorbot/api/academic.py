from fastapi_cache.decorator import cache
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.hemis_service import HemisService
from services.university_service import UniversityService
from database.db_connect import get_session
from api.dependencies import get_current_student
from database.models import Student, TgAccount
import asyncio
from datetime import datetime
from database.models import Student, Staff, TgAccount

router = APIRouter()

async def resolve_semester(student, requested_semester=None, refresh=False):
    """
    Robust semester resolution matching Bot logic.
    Prioritizes get_me for 'current' status.
    """
    if requested_semester:
        return requested_semester
        
    token = getattr(student, 'hemis_token', None)
    if not token:
        return requested_semester or "11"
        
    # Default (Joriy) - Match Bot: Try get_me first
    base_url = UniversityService.get_api_url(student.hemis_login)
    me_data = await HemisService.get_me(token, base_url=base_url)
    if me_data:
        sem = me_data.get("semester", {})
        if not sem: sem = me_data.get("currentSemester", {})
        if sem and isinstance(sem, dict):
            code = str(sem.get("code") or sem.get("id"))
            if code: return code

    # Fallback to list
    semesters = await HemisService.get_semester_list(student.hemis_token, student_id=student.id, force_refresh=refresh, base_url=base_url)
    if semesters:
        return str(semesters[0].get("code") or semesters[0].get("id"))
        
    return "11" # Absolute fallback

@router.get("/grades")
async def get_grades(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    token = getattr(student, 'hemis_token', None)

    if isinstance(student, Staff):
         return {"success": True, "data": []}

    if not token:
         return {"success": False, "message": "No Token", "data": []}

    base_url = UniversityService.get_api_url(student.hemis_login)
    if await HemisService.check_auth_status(token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    sem_code = await resolve_semester(student, semester, refresh=refresh)
    base_url = UniversityService.get_api_url(student.hemis_login)

    subjects_data = await HemisService.get_student_subject_list(
        token, 
        semester_code=sem_code, 
        student_id=student.id,
        force_refresh=refresh,
        base_url=base_url
    )

    results = []
    for item in (subjects_data or []):
        subject_info = item.get("curriculumSubject", {})
        sub_details = subject_info.get("subject", {})
        name = sub_details.get("name") or item.get("subject", {}).get("name", "Nomsiz fan")
        s_id = sub_details.get("id") or item.get("subject", {}).get("id")

        detailed_dict = HemisService.parse_grades_detailed(item)
        on = detailed_dict.get("ON", {"val_5": 0, "raw": 0})
        yn = detailed_dict.get("YN", {"val_5": 0, "raw": 0})
        jn = detailed_dict.get("JN", {"val_5": 0, "raw": 0})
        
        # Convert to list for frontend compatibility
        detailed_list = [v for k, v in detailed_dict.items() if k in ["JN", "ON", "YN"]]

        results.append({
            "id": s_id, "subject": name, "name": name,
            "overall_grade": item.get("overallScore", {}).get("grade", 0),
            "on": on, "yn": yn, "jn": jn, "detailed": detailed_list
        })
    return {"success": True, "data": results}

@router.get("/semesters")
async def get_semesters(
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if isinstance(student, Staff):
        # Staff don't have semesters in Student API
        return {"success": True, "data": []}

    if not student.hemis_token:
        return {"success": False, "message": "No Token"}

    base_url = UniversityService.get_api_url(student.hemis_login)
    if await HemisService.check_auth_status(student.hemis_token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    # 1. Fetch Real Semesters from Profile & List
    base_url = UniversityService.get_api_url(student.hemis_login)
    me_data = await HemisService.get_me(student.hemis_token, base_url=base_url)
    semesters = await HemisService.get_semester_list(student.hemis_token, student_id=student.id, force_refresh=refresh, base_url=base_url)
    
    current_code = None
    if me_data:
        sem = me_data.get("semester", {})
        if not sem: sem = me_data.get("currentSemester", {})
        if sem and isinstance(sem, dict):
            current_code = str(sem.get("code") or sem.get("id"))

    # 2. Merge and Deduplicate
    all_sems = {}
    for s in (semesters or []):
        code = str(s.get("code") or s.get("id"))
        all_sems[code] = {
            "code": code,
            "id": code,
            "name": s.get("name") or f"{int(code)-10 if int(code)>10 else code}-semestr",
            "current": False
        }
    
    # Ensure current is present
    if current_code and current_code not in all_sems:
        all_sems[current_code] = {
            "code": current_code,
            "id": current_code,
            "name": f"{int(current_code)-10 if int(current_code)>10 else current_code}-semestr",
            "current": True
        }
    elif current_code:
        all_sems[current_code]["current"] = True

    # 3. Sort and Filter
    # We show ALL past semesters + Current (labelled "Joriy")
    # We ignore future semesters
    final_list = []
    
    # Sort all found semesters descending by code
    sorted_codes = sorted(all_sems.keys(), key=lambda x: int(x), reverse=True)
    
    for code in sorted_codes:
        # Skip future semesters if we know the current one
        # ALSO Skip current semester because Frontend adds "Joriy" button automatically
        if current_code and int(code) >= int(current_code):
            continue
            
        item = all_sems[code].copy()
        
        # Calculate pretty number (e.g., 11 -> 1, 12 -> 2)
        try:
            num = int(code)
            if num > 10: num -= 10
        except:
            num = code

        if current_code and code == current_code:
            item["name"] = "Joriy"
            item["current"] = True
        else:
            item["name"] = f"{num}-semestr"
            item["current"] = False
            
        final_list.append(item)

    return {"success": True, "data": final_list}

@router.get("/subjects")
async def get_subjects(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if isinstance(student, Staff):
         return {"success": True, "data": []}

    if not getattr(student, 'hemis_token', None):
        return {"success": False, "message": "No Token"}

    base_url = UniversityService.get_api_url(student.hemis_login)
    if await HemisService.check_auth_status(student.hemis_token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    sem_code = await resolve_semester(student, semester, refresh=refresh)
    base_url = UniversityService.get_api_url(student.hemis_login)
    
    subjects_task = HemisService.get_student_subject_list(student.hemis_token, semester_code=sem_code, student_id=student.id, force_refresh=refresh, base_url=base_url)
    absence_task = HemisService.get_student_absence(student.hemis_token, semester_code=sem_code, student_id=student.id, force_refresh=refresh, base_url=base_url)
    schedule_task = HemisService.get_student_schedule_cached(student.hemis_token, semester_code=sem_code, student_id=student.id, force_refresh=refresh, base_url=base_url)
    
    subjects_data, attendance_result, schedule_data = await asyncio.gather(
        subjects_task, absence_task, schedule_task
    )

    
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
        detailed_dict = HemisService.parse_grades_detailed(item)
        on = detailed_dict.get("ON", {"val_5": 0, "raw": 0})
        yn = detailed_dict.get("YN", {"val_5": 0, "raw": 0})
        jn = detailed_dict.get("JN", {"val_5": 0, "raw": 0})
        
        # Convert to list for frontend compatibility
        detailed_list = [v for k, v in detailed_dict.items() if k in ["JN", "ON", "YN"]]
        
        results.append({
            "id": s_id, "name": name, "lecturer": t_info.get("lecturer"),
            "seminar": t_info.get("seminar"), "absent_hours": abs_map.get(name_lower, 0),
            "overall_grade": item.get("overallScore", {}).get("grade", 0),
            "grades": {"ON": on, "YN": yn, "JN": jn, "detailed": detailed_list}
        })
    return {"success": True, "data": results}

@router.get("/schedule")
async def get_schedule(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if isinstance(student, Staff):
        return {"success": True, "data": []}

    token = getattr(student, 'hemis_token', None)
    if not token:
        return {"success": False, "message": "No Token"}

    base_url = UniversityService.get_api_url(student.hemis_login)
    if await HemisService.check_auth_status(token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    sem_code = await resolve_semester(student, semester, refresh=refresh)
    schedule_data = await HemisService.get_student_schedule_cached(
        token, semester_code=sem_code, student_id=student.id, force_refresh=refresh, base_url=base_url
    )


    if not schedule_data: return {"success": True, "data": []}

    # Filter to Current Week (Monday - Sunday)
    try:
        from datetime import timedelta
        now = datetime.now()
        # Find Monday (0)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        # Find Sunday (6)
        end_of_week = start_of_week + timedelta(days=6)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_ts = start_of_week.timestamp()
        end_ts = end_of_week.timestamp()
        
        filtered_data = []
        for item in schedule_data:
            l_date = item.get("lesson_date")
            if l_date and start_ts <= l_date <= end_ts:
                filtered_data.append(item)
        
        schedule_data = filtered_data
    except Exception as e:
        logger.error(f"Schedule filter error: {e}")

    lessons_by_group = {}
    for item in schedule_data:
        s_id, t_type = str(item.get("subject", {}).get("id") or ""), str(item.get("trainingType", {}).get("code") or "")
        if not s_id: continue
        key = (s_id, t_type)
        if key not in lessons_by_group: lessons_by_group[key] = []
        lessons_by_group[key].append(item)

    for key, group in lessons_by_group.items():
        group.sort(key=lambda x: (int(x.get("lesson_date") or 0), x.get("start_time") or ""))

    unique_subjects = set(k[0] for k in lessons_by_group.keys())
    base_url = UniversityService.get_api_url(student.hemis_login)
    for s_id in unique_subjects:
        for t_code in set(k[1] for k in lessons_by_group.keys() if k[0] == s_id):
            topics = await HemisService.get_curriculum_topics(token, subject_id=s_id, semester_code=sem_code, training_type_code=t_code, student_id=student.id, base_url=base_url)

            if topics:
                group = lessons_by_group[(s_id, t_code)]
                for idx, lesson_item in enumerate(group):
                    current_topic = lesson_item.get("lesson_topic") or lesson_item.get("theme") or ""
                    if (not current_topic or current_topic == "Mavzu kiritilmagan") and idx < len(topics):
                        lesson_item["lesson_topic"] = topics[idx].get("name") or lesson_item.get("lesson_topic")
    return {"success": True, "data": schedule_data}

@router.get("/attendance")
async def get_attendance(
    semester: str = None,
    refresh: bool = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    if isinstance(student, Staff):
        return {"success": True, "data": {"total": 0, "excused": 0, "unexcused": 0, "items": []}}

    token = getattr(student, 'hemis_token', None)
    if not token:
        return {"success": False, "message": "No Token"}

    base_url = UniversityService.get_api_url(student.hemis_login)
    if await HemisService.check_auth_status(token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    sem_code = await resolve_semester(student, semester, refresh=refresh)
    base_url = UniversityService.get_api_url(student.hemis_login)
    
    try:
        _, _, _, data = await HemisService.get_student_absence(
            token, semester_code=sem_code, student_id=student.id, force_refresh=refresh, base_url=base_url
        )

        
        parsed = []
        for item in (data or []):
            hours = item.get("absent_on", 0) + item.get("absent_off", 0)
            if hours == 0: hours = item.get("hour", 2)
            parsed.append({
                "subject": item.get("subject", {}).get("name", "Fan"),
                "date": datetime.fromtimestamp(item.get("lesson_date")).strftime("%Y-%m-%d") if item.get("lesson_date") else "",
                "theme": item.get("trainingType", {}).get("name", ""), "hours": hours, "is_excused": item.get("explicable", False)
            })

        total = sum(p['hours'] for p in parsed)
        excused = sum(p['hours'] for p in parsed if p['is_excused'])
        return {"success": True, "data": {"total": total, "excused": excused, "unexcused": total - excused, "items": parsed}}
    except Exception as e:
        logger.error(f"Attendance error for student {student.id}: {e}")
        return {"success": True, "data": {"total": 0, "excused": 0, "unexcused": 0, "items": []}}

@router.get("/resources/{subject_id}")
async def get_resources(subject_id: str, student: Student = Depends(get_current_student)):
    if isinstance(student, Staff):
        return {"success": True, "data": []}

    token = getattr(student, 'hemis_token', None)
    base_url = UniversityService.get_api_url(student.hemis_login)
    if not token or await HemisService.check_auth_status(token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    resources = await HemisService.get_student_resources(token, subject_id=subject_id, base_url=base_url)

    parsed = []
    for res in resources:
        topics = []
        for item in res.get("subjectFileResourceItems", []):
            for f in item.get("files", []):
                topics.append({"id": item.get("id"), "name": f.get("name") or "Fayl", "url": f.get("url")})
        parsed.append({"id": res.get("id"), "title": res.get("title") or "Mavzu", "files": topics})
    return {"success": True, "data": parsed}

@router.get("/subject/{subject_id}/details")
async def get_subject_details_endpoint(subject_id: str, semester: str = None, student: Student = Depends(get_current_student)):
    if isinstance(student, Staff):
        return {"success": False, "message": "Xodimlar uchun mavjud emas"}

    token = getattr(student, 'hemis_token', None)
    base_url = UniversityService.get_api_url(student.hemis_login)
    if not token or await HemisService.check_auth_status(token, base_url=base_url) == "AUTH_ERROR":
        raise HTTPException(status_code=401, detail="HEMIS_AUTH_ERROR")

    subjects = await HemisService.get_student_subject_list(token, semester_code=semester, student_id=student.id, base_url=base_url)

    target_subject = next((s for s in subjects if str(s.get("subject", {}).get("id") or s.get("curriculumSubject",{}).get("subject",{}).get("id")) == str(subject_id)), None)
    
    if not target_subject: return {"success": False, "message": "Fan topilmadi"}

    detailed_dict = HemisService.parse_grades_detailed(target_subject)
    # Convert to list for frontend
    detailed_list = [v for k, v in detailed_dict.items() if k in ["JN", "ON", "YN"]]
    
    schedule = await HemisService.get_student_schedule_cached(token, semester_code=semester, student_id=student.id, base_url=base_url)
    teachers = {item.get("employee", {}).get("name") for item in schedule if str(item.get("subject", {}).get("id")) == str(subject_id) if item.get("employee", {}).get("name")}
    _, _, _, absence_items = await HemisService.get_student_absence(token, semester_code=semester, student_id=student.id, base_url=base_url)

    
    subject_absence = [{"date": datetime.fromtimestamp(item.get("lesson_date")).strftime("%d.%m.%Y") if item.get("lesson_date") else "", "hours": item.get("absent_on", 0) + item.get("absent_off", 0) or item.get("hour", 2)} for item in absence_items if str(item.get("subject", {}).get("id")) == str(subject_id)]
    
    return {"success": True, "data": {"subject": {"name": target_subject.get("subject", {}).get("name"), "grades": {"overall": target_subject.get("overallScore", {}).get("grade", 0), "detailed": detailed_list}}, "teachers": list(teachers), "attendance": {"total_missed": sum(a['hours'] for a in subject_absence), "details": subject_absence}}}
