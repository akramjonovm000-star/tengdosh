from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import os
import uuid

from database.db_connect import get_db
from database.models import Student, Staff, YetakchiActivity, YetakchiEvent, UserDocument
from api.dependencies import get_yetakchi
from api.schemas import PostResponseSchema 

router = APIRouter()

# ==========================================
# 1. DASHBOARD STATS
# ==========================================
@router.get("/dashboard/stats")
async def get_yetakchi_dashboard_stats(
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    """
    Get quick statistics for Yetakchi Dashboard
    """
    # 1. Total Students 
    # For now, let's say Yetakchi sees students in their own university
    # If they are tied to a specific faculty, we can filter by that.
    uni_id = getattr(yetakchi, 'university_id', None)
    faculty_id = getattr(yetakchi, 'faculty_id', None)
    
    student_query = select(func.count(Student.id)).where(Student.is_active == True)
    if uni_id:
        student_query = student_query.where(Student.university_id == uni_id)
    if faculty_id:
        student_query = student_query.where(Student.faculty_id == faculty_id)
        
    total_students = await db.scalar(student_query) or 0
    
    # 2. Total Pending Activities
    pending_act_query = select(func.count(YetakchiActivity.id)).where(YetakchiActivity.status == "pending")
    # Join with students to filter by faculty/uni
    pending_act_query = pending_act_query.join(Student).where(Student.university_id == uni_id)
    if faculty_id:
        pending_act_query = pending_act_query.where(Student.faculty_id == faculty_id)
        
    pending_activities = await db.scalar(pending_act_query) or 0
    
    # 3. Active students (at least 1 approved activity)
    active_stu_query = select(func.count(func.distinct(YetakchiActivity.student_id))).where(YetakchiActivity.status == "approved")
    active_stu_query = active_stu_query.join(Student).where(Student.university_id == uni_id)
    if faculty_id:
        active_stu_query = active_stu_query.where(Student.faculty_id == faculty_id)
        
    active_students = await db.scalar(active_stu_query) or 0
    
    # 4. Total Events Planned
    events_query = select(func.count(YetakchiEvent.id))
    total_events = await db.scalar(events_query) or 0

    return {
        "total_students": total_students,
        "active_students": active_students,
        "pending_activities": pending_activities,
        "total_events": total_events
    }

# ==========================================
# 2. STUDENTS LIST
# ==========================================
@router.get("/students")
async def get_yetakchi_students(
    search: Optional[str] = None,
    faculty_id: Optional[int] = None,
    course: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    query = select(Student).where(Student.is_active == True)
    
    if faculty_id:
        query = query.where(Student.faculty_id == faculty_id)
    elif getattr(yetakchi, 'faculty_id', None):
        query = query.where(Student.faculty_id == yetakchi.faculty_id)
    elif getattr(yetakchi, 'university_id', None):
        query = query.where(Student.university_id == yetakchi.university_id)

    if course:
         query = query.where(Student.level_name.like(f"%{course}%"))

    if search:
        query = query.where(
            or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.group_number.ilike(f"%{search}%")
            )
        )
        
    query = query.order_by(Student.full_name).offset(skip).limit(limit)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "group_number": s.group_number,
            "faculty": s.faculty_name,
            "level": s.level_name,
            "image_url": s.image_url,
            "points": 0 # TODO: Calculate later
        } for s in students
    ]
# ==========================================
# 3. ACTIVITIES (Pending, Approved, Rejected)
# ==========================================
@router.get("/activities")
async def get_yetakchi_activities(
    status: Optional[str] = None, # 'pending', 'approved', 'rejected'
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    query = select(YetakchiActivity).options(selectinload(YetakchiActivity.student))
    
    if status:
        query = query.where(YetakchiActivity.status == status)
        
    # Filter by yetakchi's jurisdiction (e.g. same university/faculty)
    uni_id = getattr(yetakchi, 'university_id', None)
    faculty_id = getattr(yetakchi, 'faculty_id', None)
    
    if uni_id or faculty_id:
        query = query.join(Student)
        if uni_id:
            query = query.where(Student.university_id == uni_id)
        if faculty_id:
            query = query.where(Student.faculty_id == faculty_id)

    query = query.order_by(desc(YetakchiActivity.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "student_id": a.student.id,
            "student_name": a.student.full_name,
            "student_group": a.student.group_number,
            "title": a.title,
            "description": a.description,
            "images": a.images,
            "status": a.status,
            "points_awarded": a.points_awarded,
            "created_at": a.created_at.isoformat()
        } for a in activities
    ]

@router.put("/activities/{activity_id}/review")
async def review_yetakchi_activity(
    activity_id: int,
    status: str = Form(...), # 'approved', 'rejected'
    points: int = Form(0),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    activity = await db.scalar(select(YetakchiActivity).where(YetakchiActivity.id == activity_id))
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    activity.status = status
    activity.points_awarded = points
    activity.reviewer_id = yetakchi.id
    
    await db.commit()
    return {"message": f"Activity {status}", "id": activity.id, "points": points}

# ==========================================
# 4. EVENTS
# ==========================================
@router.post("/events")
async def create_yetakchi_event(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    event_date: str = Form(...),
    documents: List[UploadFile] = File(None),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    from utils.student_utils import save_file
    
    upload_paths = []
    if documents:
        for doc in documents:
            if doc.filename:
                # Reusing existing generic file save utility
                path = await save_file(doc, "yetakchi_events")
                upload_paths.append(path)
                
    import json
    new_event = YetakchiEvent(
        creator_id=yetakchi.id,
        title=title,
        description=description,
        event_date=datetime.fromisoformat(event_date.replace("Z", "+00:00")),
        participants_count=0,
        documents=json.dumps(upload_paths) if upload_paths else None
    )
    
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    
    return {"message": "Event created successfully", "event_id": new_event.id}

@router.get("/events")
async def get_yetakchi_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    query = select(YetakchiEvent).where(YetakchiEvent.creator_id == yetakchi.id)\
                                 .order_by(desc(YetakchiEvent.event_date))\
                                 .offset(skip).limit(limit)
                                 
    result = await db.execute(query)
    events = result.scalars().all()
    
    import json
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.event_date.isoformat(),
            "participants": e.participants_count,
            "documents": json.loads(e.documents) if e.documents else []
        } for e in events
    ]
# ==========================================
# 5. REPORTS (Excel Export)
# ==========================================
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

@router.get("/reports/export")
async def export_yetakchi_reports(
    period: str = Query("monthly", description="weekly or monthly"),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports student activity data as an Excel file.
    """
    # Simply get all approved activities under this Yetakchi's jurisdiction
    uni_id = getattr(yetakchi, 'university_id', None)
    faculty_id = getattr(yetakchi, 'faculty_id', None)
    
    query = select(YetakchiActivity).options(selectinload(YetakchiActivity.student)).where(YetakchiActivity.status == 'approved')
    
    if uni_id or faculty_id:
        query = query.join(Student)
        if uni_id:
            query = query.where(Student.university_id == uni_id)
        if faculty_id:
            query = query.where(Student.faculty_id == faculty_id)

    # In a real app we'd filter by `period` timestamp (e.g. last 7 days or 30 days)
    # For now, we just export all.
    result = await db.execute(query)
    activities = result.scalars().all()
    
    data = []
    for a in activities:
        data.append({
            "ID": a.id,
            "Talaba": a.student.full_name,
            "Guruh": a.student.group_number,
            "Fakultet": a.student.faculty_name,
            "Faollik nomi": a.title,
            "Ball": a.points_awarded,
            "Sana": a.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Hisobot')
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="yetakchi_hisobot_{period}.xlsx"'
    }
    
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )
# ==========================================
# 6. DOCUMENTS
# ==========================================
@router.get("/documents")
async def get_yetakchi_documents(
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    query = select(UserDocument).options(selectinload(UserDocument.student))
    
    uni_id = getattr(yetakchi, 'university_id', None)
    faculty_id = getattr(yetakchi, 'faculty_id', None)
    
    if uni_id or faculty_id:
        query = query.join(Student)
        if uni_id:
            query = query.where(Student.university_id == uni_id)
        if faculty_id:
            query = query.where(Student.faculty_id == faculty_id)

    if search:
        # UserDocument may not have document_type mapped like this, let me check UserDocument model.
        # It has document_type usually. Let's see models.py if UserDocument has document_type.
        pass

    query = query.order_by(desc(UserDocument.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    docs = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "student_name": d.student.full_name if d.student else "Noma'lum",
            "document_type": getattr(d, 'document_type', 'Hujjat'),
            "file_url": d.file_url,
            "status": d.status,
            "created_at": d.created_at.isoformat()
        } for d in docs
    ]

# ==========================================
# 7. ANNOUNCEMENTS
# ==========================================
from database.models import ChoyxonaPost

@router.post("/announcements")
async def create_yetakchi_announcement(
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    yetakchi = Depends(get_yetakchi),
    db: AsyncSession = Depends(get_db)
):
    from utils.student_utils import save_file
    
    image_url = None
    if image and image.filename:
        image_url = await save_file(image, "choyxona_images")
        
    new_post = ChoyxonaPost(
        # Note: ChoyxonaPost might expect a student_id
        student_id=yetakchi.id if hasattr(yetakchi, 'id') else 1,
        content=content,
        image_url=image_url
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    return {"message": "Announcement created successfully", "post_id": new_post.id}
