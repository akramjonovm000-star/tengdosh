from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database.db_connect import get_db
from database.models import Student, StudentFeedback, Faculty
from api.dependencies import get_current_student
from pydantic import BaseModel

router = APIRouter(prefix="/management/appeals", tags=["Management Appeals"])

@router.get("/stats")
async def get_appeals_stats(
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # 1. Auth Check
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
    uni_id = getattr(staff, 'university_id', None)
    if not uni_id:
        # Fallback if university_id missing (superuser?)
        return {"error": "University ID not found"}
    
    # 2. Overall Counts
    stmt = select(StudentFeedback.status, func.count(StudentFeedback.id)).join(Student)\
        .where(Student.university_id == uni_id).group_by(StudentFeedback.status)
    rows = (await db.execute(stmt)).all()
    
    counts = {"pending": 0, "processing": 0, "resolved": 0, "replied": 0}
    total = 0
    for status, count in rows:
        # Normalized status check if needed
        s = status.lower() if status else "pending"
        counts[s] = count
        total += count
        
    # 3. Faculty Performance
    # Using existing snapshot 'student_faculty' in StudentFeedback
    fac_stmt = select(StudentFeedback.student_faculty, StudentFeedback.status, func.count(StudentFeedback.id))\
        .join(Student).where(Student.university_id == uni_id)\
        .group_by(StudentFeedback.student_faculty, StudentFeedback.status)
        
    fac_rows = (await db.execute(fac_stmt)).all()
    
    fac_stats = {}
    for fac, status, count in fac_rows:
        if not fac: fac = "Boshqa"
        
        if fac not in fac_stats: 
            fac_stats[fac] = {"total": 0, "resolved": 0, "pending": 0}
            
        fac_stats[fac]["total"] += count
        
        if status in ['resolved', 'replied']:
             fac_stats[fac]["resolved"] += count
        else:
             fac_stats[fac]["pending"] += count
             
    faculty_performance = []
    for fac, data in fac_stats.items():
        rate = (data["resolved"] / data["total"]) * 100 if data["total"] > 0 else 0
        faculty_performance.append({
            "faculty": fac,
            "total": data["total"],
            "resolved": data["resolved"],
            "pending": data["pending"],
            "rate": round(rate, 1)
        })
    
    # Sort by total appeals descending
    faculty_performance.sort(key=lambda x: x["total"], reverse=True)
    
    # 4. Top Targets (Who is receiving appeals?)
    role_stmt = select(StudentFeedback.assigned_role, func.count(StudentFeedback.id))\
        .join(Student).where(Student.university_id == uni_id)\
        .group_by(StudentFeedback.assigned_role)
    role_rows = (await db.execute(role_stmt)).all()
    
    top_targets = [{"role": r or "Noma'lum", "count": c} for r, c in role_rows]
    top_targets.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total": total,
        "counts": counts,
        "faculty_performance": faculty_performance,
        "top_targets": top_targets
    }

@router.get("/list")
async def get_appeals_list(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    faculty: Optional[str] = None,
    ai_topic: Optional[str] = None,
    assigned_role: Optional[str] = None,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Auth Check
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
    
    uni_id = getattr(staff, 'university_id', None)
    
    query = select(StudentFeedback).join(Student).where(Student.university_id == uni_id)
    
    if status:
        if status == 'active': # Custom filter for Pending+Processing
             query = query.where(StudentFeedback.status.in_(['pending', 'processing']))
        # Special case for "resolved" to include "replied"
        elif status == 'resolved':
             query = query.where(StudentFeedback.status.in_(['resolved', 'replied']))
        else:
             query = query.where(StudentFeedback.status == status)
             
    if faculty:
        if faculty == "Boshqa":
             query = query.where(or_(StudentFeedback.student_faculty == None, StudentFeedback.student_faculty == ""))
        else:
             query = query.where(StudentFeedback.student_faculty == faculty)
        
    if ai_topic:
        query = query.where(StudentFeedback.ai_topic == ai_topic)

    if assigned_role:
        query = query.where(StudentFeedback.assigned_role == assigned_role)
        
    # Order by newest
    query = query.order_by(StudentFeedback.created_at.desc())
    
    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    res = await db.execute(query)
    appeals = res.scalars().all()
    
    return [
        {
            "id": a.id,
            "text": a.text,
            "status": a.status,
            "student_name": a.student_full_name or "Noma'lum", 
            "student_faculty": a.student_faculty or "Noma'lum",
            "student_group": a.student_group,
            "student_phone": a.student_phone,
            "ai_topic": a.ai_topic,
            "created_at": a.created_at.isoformat(),
            "assigned_role": a.assigned_role or "Umumiy",
            "is_anonymous": a.is_anonymous
        } for a in appeals
    ]

@router.post("/{id}/resolve")
async def resolve_appeal(
    id: int,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    stmt = select(StudentFeedback).where(StudentFeedback.id == id)
    appeal = (await db.execute(stmt)).scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(404, "Murojaat topilmadi")
        
    appeal.status = 'resolved'
    appeal.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"success": True, "message": "Murojaat yopildi"}
