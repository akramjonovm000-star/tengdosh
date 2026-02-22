import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff, ChoyxonaPost
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from utils.moderators import is_global_moderator

async def main():
    async with AsyncSessionLocal() as db:
        # Get Sanjar 84
        student = await db.get(Staff, 84)
        print(f"Sanjar: {student.full_name}, uni={student.university_id}, fac={student.faculty_id}, role={student.role}")

        category = 'university'
        faculty_id = None
        specialty_name = None
        skip, limit = 0, 20
        
        # from get_posts logic
        query = select(ChoyxonaPost).options(
            selectinload(ChoyxonaPost.student),
            selectinload(ChoyxonaPost.staff)
        ).order_by(desc(ChoyxonaPost.created_at))
        query = query.where(ChoyxonaPost.category_type == category)
        
        uni_id = getattr(student, 'university_id', None) or 1
        f_id = getattr(student, 'faculty_id', None)
        
        is_staff = True
        staff_role = student.role
        is_management = True
        is_global_mgmt = staff_role in ['owner', 'developer', 'rektor', 'prorektor', 'yoshlar_prorektori', 'rahbariyat']
        print(f"mgmt={is_management} global={is_global_mgmt}")
        
        login_raw = getattr(student, 'hemis_login', None) or getattr(student, 'hemis_id', None)
        login = str(login_raw or '').strip()
        is_moderator = is_global_moderator(login)
        print(f"mod={is_moderator} login={login}")
        
        if category == 'university':
             if not is_moderator:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)

        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        posts = result.scalars().all()
        print(f"Found {len(posts)} posts for university")
        for p in posts:
            print(f"- Post {p.id}: {p.category_type}")
            
        # FACULTY CATEGORY
        # ... just skip, verify university first

asyncio.run(main())
