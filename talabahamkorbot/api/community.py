from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List

from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff, ChoyxonaPost, ChoyxonaPostLike, ChoyxonaPostRepost, ChoyxonaComment, ChoyxonaPostView
from api.dependencies import get_current_student, get_student_or_staff, get_db, require_action_token
from utils.student_utils import format_name
from api.schemas import PostCreateSchema, PostResponseSchema, CommentCreateSchema, CommentResponseSchema
from services.notification_service import NotificationService
from database.models import ChoyxonaCommentLike # Fix for NameError

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/posts", response_model=PostResponseSchema)
async def create_post(
    data: PostCreateSchema,
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post with strict context binding.
    """
    # Fix for Staff who use this endpoint
    student_id = getattr(student, 'id', None)
    full_name = getattr(student, 'full_name', "System User")
    username = getattr(student, 'username', None)
    image_url = getattr(student, 'image_url', None)
    is_premium = getattr(student, 'is_premium', False)
    custom_badge = getattr(student, 'custom_badge', None)

    # 1. Determine Context based on Category
    uni_id = getattr(student, 'university_id', None) or 1
    target_uni = uni_id
    target_fac = None
    target_spec = None
    
    from database.models import Staff
    is_staff = isinstance(student, Staff)
    staff_role = getattr(student, 'role', None) if is_staff else None
    
    is_management = False
    is_global_mgmt = False
    
    if is_staff:
        is_management = True
        if staff_role in ['owner', 'developer', 'rektor', 'prorektor', 'yoshlar_prorektori', 'rahbariyat']:
            is_global_mgmt = True
    else:
         is_management = getattr(student, 'hemis_role', None) == 'rahbariyat' or getattr(student, 'role', None) == 'rahbariyat'

    category = data.category_type
    
    if category == 'university':
        target_uni = uni_id
        
    elif category == 'faculty':
        target_uni = uni_id
        f_id = getattr(student, 'faculty_id', None)
        if is_management:
            if f_id:
                target_fac = f_id
            elif data.target_faculty_id:
                target_fac = data.target_faculty_id
            elif not is_global_mgmt:
                 target_fac = f_id
        else:
            target_fac = getattr(student, 'faculty_id', None)
            
        if not target_fac and not is_global_mgmt:
            raise HTTPException(status_code=400, detail="Sizda fakultet biriktirilmagan")
            
    elif category == 'specialty':
        target_uni = uni_id
        f_id = getattr(student, 'faculty_id', None)
        if is_management:
            if f_id:
                target_fac = f_id
            else:
                target_fac = data.target_faculty_id or getattr(student, 'faculty_id', None)
                
            target_spec = data.target_specialty_name or getattr(student, 'specialty_name', None)
        else:
            target_fac = getattr(student, 'faculty_id', None)
            target_spec = getattr(student, 'specialty_name', None)
            
        if not target_spec and not is_global_mgmt:
             raise HTTPException(status_code=400, detail="Sizda mutaxassislik (yo'nalish) ma'lumoti yo'q")
    else:
         raise HTTPException(status_code=400, detail="Noto'g'ri kategoriya")
    
    # 2. Create Post
    is_staff = isinstance(student, Staff)
    new_post = ChoyxonaPost(
        student_id=student.id if not is_staff else None,
        staff_id=student.id if is_staff else None,
        content=data.content,
        category_type=category,
        target_university_id=target_uni,
        target_faculty_id=target_fac,
        target_specialty_name=target_spec
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    # [NEW] Log Activity
    from services.activity_service import ActivityService, ActivityType
    await ActivityService.log_activity(
        db=db,
        user_id=student.id,
        role='staff' if is_staff else 'student',
        activity_type=ActivityType.POST,
        ref_id=new_post.id
    )
    
    # Re-fetch with author to map response
    # Or just use the student object we have
    # Manually construct response to avoid lazy loading 'likes' on async session
    return PostResponseSchema(
        id=new_post.id,
        content=new_post.content,
        category_type=new_post.category_type,
        author_id=student.id,
        author_name=full_name,
        author_username=username,
        author_avatar=image_url,
        author_role=getattr(student, 'hemis_role', None) or getattr(student, 'role', 'Talaba'),
        created_at=new_post.created_at,
        target_university_id=new_post.target_university_id,
        target_faculty_id=new_post.target_faculty_id,
        target_specialty_name=new_post.target_specialty_name,
        likes_count=0,
        is_liked_by_me=False,
        views_count=0,
        author_is_premium=is_premium,
        author_custom_badge=custom_badge
    )

@router.get("/filters/meta")
async def get_filters_meta(
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get faculties and specialties for filtering within the university.
    """
    uni_id = student.university_id
    if not uni_id:
        return {"faculties": [], "specialties": []}
    
    # 1. Get Faculties
    from database.models import Faculty
    f_id = getattr(student, 'faculty_id', None)
    
    fac_query = select(Faculty.id, Faculty.name).where(Faculty.university_id == uni_id, Faculty.is_active == True)
    if f_id:
        fac_query = fac_query.where(Faculty.id == f_id)
        
    fac_result = await db.execute(fac_query)
    faculties = [{"id": r[0], "name": r[1]} for r in fac_result.all()]
    
    # 2. Get Distinct Specialties
    spec_query = select(Student.specialty_name).where(
        Student.university_id == uni_id, 
        Student.specialty_name.isnot(None),
        Student.specialty_name != ""
    )
    if f_id:
        spec_query = spec_query.where(Student.faculty_id == f_id)
        
    spec_result = await db.execute(spec_query.distinct())
    specialties = [r[0] for r in spec_result.all()]
    specialties.sort()
    
    return {
        "faculties": faculties,
        "specialties": specialties
    }

@router.get("/posts", response_model=List[PostResponseSchema])
async def get_posts(
    category: str = Query(..., description="university, faculty, specialty"),
    faculty_id: int = Query(None),
    specialty_name: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get posts with strict access control filtering.
    """
    try:
        # Create valid query
        query = select(ChoyxonaPost).options(
            selectinload(ChoyxonaPost.student),
            selectinload(ChoyxonaPost.staff)
        ).order_by(desc(ChoyxonaPost.created_at))
        
        # 1. Category Filter (Tab Filter)
        query = query.where(ChoyxonaPost.category_type == category)
        
        uni_id = getattr(student, 'university_id', None) or 1
        f_id = getattr(student, 'faculty_id', None)
        
        from database.models import Staff
        is_staff = isinstance(student, Staff)
        staff_role = getattr(student, 'role', None) if is_staff else None
        
        is_management = False
        is_global_mgmt = False
        
        if is_staff:
            is_management = True
            # We consider owners and high level mgmt as global
            if staff_role in ['owner', 'developer', 'rektor', 'prorektor', 'yoshlar_prorektori', 'rahbariyat']:
                is_global_mgmt = True
        else:
             is_management = getattr(student, 'hemis_role', None) == 'rahbariyat' or getattr(student, 'role', None) == 'rahbariyat'
        
        # MODERATOR CHECK
        from utils.moderators import is_global_moderator
        login_raw = getattr(student, 'hemis_login', None) or getattr(student, 'hemis_id', None)
        login = str(login_raw or '').strip()
        is_moderator = is_global_moderator(login)
        if not is_moderator and (login == '395251101397' or getattr(student, 'id', 0) == 730):
             is_moderator = True

        if category == 'university': 
             if not is_moderator:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)
        
        elif category == 'faculty':
             if is_moderator or is_global_mgmt:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)
                 if faculty_id:
                     query = query.where(ChoyxonaPost.target_faculty_id == faculty_id)
             elif is_management:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)
                 if f_id:
                     query = query.where(ChoyxonaPost.target_faculty_id == f_id)
                 elif faculty_id:
                     query = query.where(ChoyxonaPost.target_faculty_id == faculty_id)
             else:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)
                 if faculty_id:
                    query = query.where(ChoyxonaPost.target_faculty_id == faculty_id)
                 elif f_id:
                    query = query.where(ChoyxonaPost.target_faculty_id == f_id)

        elif category == 'specialty':
             if is_moderator or is_global_mgmt:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)
                 if faculty_id:
                     query = query.where(ChoyxonaPost.target_faculty_id == faculty_id)
                 if specialty_name:
                     query = query.where(ChoyxonaPost.target_specialty_name == specialty_name)
             else:
                 query = query.where(ChoyxonaPost.target_university_id == uni_id)
                 if is_management:
                     if f_id:
                         query = query.where(ChoyxonaPost.target_faculty_id == f_id)
                 elif f_id:
                     query = query.where(ChoyxonaPost.target_faculty_id == f_id)

                 if specialty_name:
                     query = query.where(ChoyxonaPost.target_specialty_name == specialty_name)
                 else:
                     s_name = getattr(student, 'specialty_name', None)
                     if s_name:
                         query = query.where(ChoyxonaPost.target_specialty_name == s_name)
             
        query = query.offset(skip).limit(limit)
            
        result = await db.execute(query)
        posts = result.scalars().all()
        
        if not posts:
            return []

        # Optimize Access: Batch fetch liked/reposted status
        post_ids = [p.id for p in posts]
        is_staff = isinstance(student, Staff)
        
        # Check Likes
        liked_ids = set()
        if post_ids:
            l_query = select(ChoyxonaPostLike.post_id).where(ChoyxonaPostLike.post_id.in_(post_ids))
            if is_staff:
                l_query = l_query.where(ChoyxonaPostLike.staff_id == student.id)
            else:
                l_query = l_query.where(ChoyxonaPostLike.student_id == student.id)
            
            l_result = await db.execute(l_query)
            liked_ids = set(l_result.scalars().all())

        # Check Reposts
        reposted_ids = set()
        if post_ids:
            r_query = select(ChoyxonaPostRepost.post_id).where(ChoyxonaPostRepost.post_id.in_(post_ids))
            if is_staff:
                r_query = r_query.where(ChoyxonaPostRepost.staff_id == student.id)
            else:
                r_query = r_query.where(ChoyxonaPostRepost.student_id == student.id)
                
            r_result = await db.execute(r_query)
            reposted_ids = set(r_result.scalars().all())
        
        
        return [_map_post_optimized(p, student, p.id in liked_ids, p.id in reposted_ids) for p in posts]
    except Exception as e:
        import traceback
        import datetime
        logger.error(f"\n--- ERROR {datetime.datetime.now()} in get_posts ---")
        logger.error(traceback.format_exc())
        logger.error("-" * 40)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts/reposted", response_model=List[PostResponseSchema])
async def get_reposted_posts(
    target_student_id: int = Query(..., description="Student ID whose reposts we want"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get posts reposted by a specific student.
    """
    # Join Reposts -> Posts -> Student (Author)
    stmt = select(ChoyxonaPost).join(ChoyxonaPostRepost).options(
        selectinload(ChoyxonaPost.student) # Only load author
    ).where(ChoyxonaPostRepost.student_id == target_student_id).order_by(desc(ChoyxonaPostRepost.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    posts = result.scalars().all()

    if not posts:
        return []
    
    # Optimize Access: Batch fetch liked/reposted status
    post_ids = [p.id for p in posts]
    
    # Check Likes
    liked_ids = set()
    if post_ids:
        l_result = await db.execute(
            select(ChoyxonaPostLike.post_id)
            .where(
                ChoyxonaPostLike.student_id == student.id,
                ChoyxonaPostLike.post_id.in_(post_ids)
            )
        )
        liked_ids = set(l_result.scalars().all())

    # Check Reposts
    reposted_ids = set()
    if post_ids:
        r_result = await db.execute(
            select(ChoyxonaPostRepost.post_id)
            .where(
                ChoyxonaPostRepost.student_id == student.id,
                ChoyxonaPostRepost.post_id.in_(post_ids)
            )
        )
        reposted_ids = set(r_result.scalars().all())
    
    return [_map_post_optimized(p, student, p.id in liked_ids, p.id in reposted_ids) for p in posts]

def format_name(student: Student):
    if not student: return "Unknown"
    
    # We want "First Last" for community posts as requested
    # Database full_name is stored as "Last First [Patronymic]"
    
    f_name = (student.full_name or "").strip()
    if f_name and len(f_name.split()) >= 2:
        parts = f_name.split()
        # parts[0] is Last, parts[1] is First
        # Return "First Last"
        from utils.text_utils import format_uzbek_name
        return format_uzbek_name(f"{parts[1]} {parts[0]}")
    
    # Fallback to short_name
    s_name = (student.short_name or "").strip()
    
    from utils.text_utils import format_uzbek_name
    if f_name: return format_uzbek_name(f_name)
    if s_name: return format_uzbek_name(s_name)
    
    return "Talaba"

def _map_post_optimized(post: ChoyxonaPost, current_user, is_liked: bool, is_reposted: bool):
    author = post.student or post.staff
    current_user_id = getattr(current_user, 'id', 0)
    is_staff_user = isinstance(current_user, Staff)
    
    # MODERATOR CHECK
    from utils.moderators import is_global_moderator
    login_raw = getattr(current_user, 'hemis_login', None) or getattr(current_user, 'hemis_id', None)
    login = str(login_raw or '').strip()
    is_moderator = is_global_moderator(login) or (current_user_id == 730)

    is_mine = False
    if is_moderator:
        is_mine = True
    elif post.staff_id and is_staff_user and post.staff_id == current_user_id:
        is_mine = True
    elif post.student_id and not is_staff_user and post.student_id == current_user_id:
        is_mine = True

    return PostResponseSchema(
        id=post.id,
        content=post.content,
        category_type=post.category_type,
        author_id=author.id if author else 0,
        author_name=format_name(author) if author else "Unknown",
        author_username=getattr(author, 'username', None),
        author_avatar=getattr(author, 'image_url', None),
        author_image=getattr(author, 'image_url', None),
        image=getattr(author, 'image_url', None),
        author_role=(getattr(author, 'hemis_role', None) or getattr(author, 'role', 'student')) if author else "student",
        author_is_premium=getattr(author, 'is_premium', False) if author else False,
        author_custom_badge=getattr(author, 'custom_badge', None) if author else None,
        created_at=post.created_at,
        target_university_id=post.target_university_id,
        target_faculty_id=post.target_faculty_id,
        target_specialty_name=post.target_specialty_name,
        
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        reposts_count=post.reposts_count,
        views_count=post.views_count,
        
        is_liked_by_me=is_liked,
        is_reposted_by_me=is_reposted,
        is_mine=is_mine
    )

@router.get("/posts/{post_id}", response_model=PostResponseSchema)
async def get_post_by_id(
    post_id: int,
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    query = select(ChoyxonaPost).options(
        selectinload(ChoyxonaPost.student) # Only load author
    ).where(ChoyxonaPost.id == post_id)
    
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
        
    # Check Like Status efficiently
    is_liked = False
    if post.likes_count > 0:
        l_result = await db.execute(
            select(ChoyxonaPostLike.id)
            .where(
                ChoyxonaPostLike.post_id == post_id,
                ChoyxonaPostLike.student_id == student.id
            ).limit(1)
        )
        is_liked = l_result.scalar_one_or_none() is not None

    # Check Repost Status efficiently
    is_reposted = False
    if post.reposts_count > 0:
        r_result = await db.execute(
            select(ChoyxonaPostRepost.id)
            .where(
                ChoyxonaPostRepost.post_id == post_id,
                ChoyxonaPostRepost.student_id == student.id
            ).limit(1)
        )
        is_reposted = r_result.scalar_one_or_none() is not None

    # --- VIEW COUNT LOGIC (30s Cooldown) ---
    is_staff = isinstance(student, Staff)
    v_query = select(ChoyxonaPostView).where(ChoyxonaPostView.post_id == post_id)
    if is_staff:
        v_query = v_query.where(ChoyxonaPostView.staff_id == student.id)
    else:
        v_query = v_query.where(ChoyxonaPostView.student_id == student.id)
    
    v_result = await db.execute(v_query.limit(1))
    existing_view = v_result.scalar_one_or_none()
    
    now = datetime.utcnow()
    should_increment = False
    
    if existing_view:
        # Check if 30 seconds passed since last view
        if (now - existing_view.viewed_at).total_seconds() >= 30:
            existing_view.viewed_at = now
            should_increment = True
    else:
        # New View
        new_view = ChoyxonaPostView(
            post_id=post_id,
            student_id=student.id if not is_staff else None,
            staff_id=student.id if is_staff else None,
            viewed_at=now
        )
        db.add(new_view)
        should_increment = True

    if should_increment:
        # Atomic increment
        post.views_count = ChoyxonaPost.views_count + 1
        await db.commit()
        await db.refresh(post)
    else:
        # Just commit any other changes (if any) or pass
        await db.commit()

    return _map_post_optimized(post, student, is_liked, is_reposted)

@router.put("/posts/{post_id}", response_model=PostResponseSchema)
async def update_post(
    post_id: int,
    data: PostCreateSchema, # Reuse create schema (content + category)
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    # Only load author (which is likely the student themselves since we check ID)
    query = select(ChoyxonaPost).where(ChoyxonaPost.id == post_id)
    
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
        
    # MODERATOR CHECK
    from utils.moderators import is_global_moderator
    login_raw = getattr(student, 'hemis_login', None) or getattr(student, 'hemis_id', None)
    login = str(login_raw or '').strip()
    is_moderator = is_global_moderator(login) or (getattr(student, 'id', 0) == 730)

    if not is_moderator and post.student_id != student.id and post.staff_id != student.id:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingizning postingizni o'zgartira olasiz")
        
    post.content = data.content
    # We generally don't allow changing category/context after creation, but content yes.
    
    await db.commit()
    await db.refresh(post)
    
    # We need to manually load relationships or just return mapped with empty lists if we know they didn't change count-wise
    # But better to just re-fetch fully if needed. For speed, assume 0 for response or existing.
    # Simple fix: return mapped with current user. 
    # Since it's the AUTHOR updating, is_liked_by_me is likely False unless they liked their own post.
    # We can check efficiently.
    
    is_liked = False
    if post.likes_count > 0:
         l_result = await db.execute(select(ChoyxonaPostLike.id).where(ChoyxonaPostLike.post_id == post_id, ChoyxonaPostLike.student_id == student.id).limit(1))
         is_liked = l_result.scalar_one_or_none() is not None

    is_reposted = False
    if post.reposts_count > 0:
         r_result = await db.execute(select(ChoyxonaPostRepost.id).where(ChoyxonaPostRepost.post_id == post_id, ChoyxonaPostRepost.student_id == student.id).limit(1))
         is_reposted = r_result.scalar_one_or_none() is not None

    return _map_post_optimized(post, student, is_liked, is_reposted)


@router.post("/posts/{post_id}/view")
async def view_post(
    post_id: int,
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Increment view count for a post.
    Has a 30-second cooldown per user per post.
    """
    # 1. Check if post exists (Optional optimization: skip check if using foreign key catch, 
    # but we need to check cooldown first anyway)
    
    # We can do this efficiently without loading the whole post if we want, 
    # but we need to check Cooldown on ChoyxonaPostView
    
    is_staff = isinstance(student, Staff)
    current_user_id = student.id
    
    # 2. Check Existing View
    v_query = select(ChoyxonaPostView).where(ChoyxonaPostView.post_id == post_id)
    if is_staff:
        v_query = v_query.where(ChoyxonaPostView.staff_id == current_user_id)
    else:
        v_query = v_query.where(ChoyxonaPostView.student_id == current_user_id)
        
    result = await db.execute(v_query.limit(1))
    existing_view = result.scalar_one_or_none()
    
    now = datetime.utcnow()
    should_increment = False
    
    if existing_view:
        # Check cooldown
        if (now - existing_view.viewed_at).total_seconds() >= 30:
            existing_view.viewed_at = now
            should_increment = True
    else:
        # Create New View
        # Check if post exists first to avoid FK error
        # Or Just try insert and catch error? Better to check existence lightly if needed.
        # But for speed, let's assuming client sends valid ID. 
        # Actually proper way:
        
        # Verify Post Exists
        # p_check = await db.execute(select(ChoyxonaPost.id).where(ChoyxonaPost.id == post_id))
        # if not p_check.scalar_one_or_none():
        #     raise HTTPException(status_code=404, detail="Post topilmadi")

        new_view = ChoyxonaPostView(
            post_id=post_id,
            student_id=current_user_id if not is_staff else None,
            staff_id=current_user_id if is_staff else None,
            viewed_at=now
        )
        db.add(new_view)
        should_increment = True
        
    if should_increment:
        # Increment Counter on Post
        # We use strict update to avoid race conditions is better, but here we can fetch-update
        # update(ChoyxonaPost).where(ChoyxonaPost.id == post_id).values(views_count=ChoyxonaPost.views_count + 1)
        
        from sqlalchemy import update
        stmt = (
            update(ChoyxonaPost)
            .where(ChoyxonaPost.id == post_id)
            .values(views_count=ChoyxonaPost.views_count + 1)
            .execution_options(synchronize_session=False)
        )
        await db.execute(stmt)
        await db.commit()
        return {"status": "incremented"}
    
    await db.commit()
    return {"status": "cooldown"}

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
        
    is_management = getattr(student, 'hemis_role', None) == 'rahbariyat' or getattr(student, 'role', None) == 'rahbariyat'
    f_id = getattr(student, 'faculty_id', None)
    
    # Permission check:
    # 1. Author can delete their own post
    # 2. Management can delete any post in their university (unless restricted by faculty)
    can_delete = False
    
    # MODERATOR CHECK
    from utils.moderators import is_global_moderator
    login_raw = getattr(student, 'hemis_login', None) or getattr(student, 'hemis_id', None)
    login = str(login_raw or '').strip()
    is_moderator = is_global_moderator(login) or (getattr(student, 'id', 0) == 730)

    if is_moderator:
        can_delete = True
    elif post.student_id == student.id or post.staff_id == student.id:
        can_delete = True
    elif is_management and post.target_university_id == student.university_id:
        if f_id:
            # Restricted management can only delete within their faculty
            if post.target_faculty_id == f_id:
                can_delete = True
        else:
            # Global management
            can_delete = True
        
    if not can_delete:
        raise HTTPException(status_code=403, detail="Sizda ushbu postni o'chirish huquqi yo'q")
        
    await db.delete(post)
    await db.commit()
    return {"status": "success", "message": "Post o'chirildi"}

@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    # Check if post exists
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")

    is_staff = isinstance(student, Staff)
    
    # Check for existing like
    l_query = select(ChoyxonaPostLike).where(ChoyxonaPostLike.post_id == post_id)
    if is_staff:
        l_query = l_query.where(ChoyxonaPostLike.staff_id == student.id)
    else:
        l_query = l_query.where(ChoyxonaPostLike.student_id == student.id)
        
    existing_like = await db.scalar(l_query)
    
    if existing_like:
        await db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1) 
        liked = False
    else:
        new_like = ChoyxonaPostLike(
            post_id=post_id, 
            student_id=student.id if not is_staff else None,
            staff_id=student.id if is_staff else None
        )
        db.add(new_like)
        post.likes_count += 1
        liked = True

        # [NEW] Log Activity
        if not is_staff: # Only log student activity for now
             from services.activity_service import ActivityService, ActivityType
             await ActivityService.log_activity(
                db=db,
                user_id=student.id,
                role='student',
                activity_type=ActivityType.LIKE,
                ref_id=post_id
             )

    await db.commit()
    return {"status": "success", "liked": liked, "count": post.likes_count}

@router.post("/posts/{post_id}/repost")
async def toggle_repost(
    post_id: int,
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaPostRepost
    # Check if post exists
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")

    is_staff = isinstance(student, Staff)
    
    # Check for existing repost
    r_query = select(ChoyxonaPostRepost).where(ChoyxonaPostRepost.post_id == post_id)
    if is_staff:
        r_query = r_query.where(ChoyxonaPostRepost.staff_id == student.id)
    else:
        r_query = r_query.where(ChoyxonaPostRepost.student_id == student.id)
        
    existing_repost = await db.scalar(r_query)
    
    if existing_repost:
        await db.delete(existing_repost)
        post.reposts_count = max(0, post.reposts_count - 1)
        reposted = False
    else:
        new_repost = ChoyxonaPostRepost(
            post_id=post_id, 
            student_id=student.id if not is_staff else None,
            staff_id=student.id if is_staff else None
        )
        db.add(new_repost)
        post.reposts_count += 1
        reposted = True

    await db.commit()
    return {"status": "success", "reposted": reposted, "count": post.reposts_count}

@router.post("/posts/{post_id}/comments", response_model=CommentResponseSchema)
async def create_comment(
    post_id: int,
    data: CommentCreateSchema,
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    # ... (same checks)
    # 1. Fetch Post to verify access logic
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
    
    # ... (access checks)
    # 2. Verify Access (User must have same context as post)
    # [FIX] Use getattr for safety (Staff vs Student)
    student_uni_id = getattr(student, 'university_id', None)
    student_fac_id = getattr(student, 'faculty_id', None)
    student_spec_name = getattr(student, 'specialty_name', None)

    if post.category_type == 'university' and post.target_university_id != student_uni_id:
        raise HTTPException(status_code=403, detail="Siz bu universitet postiga yozolmaysiz")
    
    if post.category_type == 'faculty' and (post.target_university_id != student_uni_id or post.target_faculty_id != student_fac_id):
        raise HTTPException(status_code=403, detail="Siz bu fakultet postiga yozolmaysiz")
        
    if post.category_type == 'specialty' and (post.target_specialty_name != student_spec_name):
         raise HTTPException(status_code=403, detail="Siz bu yo'nalish postiga yozolmaysiz")

    # 3. Create Comment Logic with Depth Control & Notifications
    from database.models import ChoyxonaComment, Notification, Staff
    
    final_reply_to_id = data.reply_to_comment_id
    reply_to_user_id = None
    reply_to_staff_id = None
    notification_recipient_id = None
    notification_recipient_staff_id = None
    
    if final_reply_to_id:
        parent_comment = await db.get(ChoyxonaComment, final_reply_to_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Javob berilayotgan komment topilmadi")
        
        reply_to_user_id = parent_comment.student_id
        reply_to_staff_id = parent_comment.staff_id
        notification_recipient_id = parent_comment.student_id 
        notification_recipient_staff_id = parent_comment.staff_id

    # [FIX] Safer is_staff check
    is_staff = isinstance(student, Staff) or getattr(student, 'hemis_role', None) == 'staff' or getattr(student, 'role', None) == 'staff'
    
    new_comment = ChoyxonaComment(
        post_id=post_id,
        student_id=student.id if not is_staff else None,
        staff_id=student.id if is_staff else None,
        content=data.content,
        reply_to_comment_id=final_reply_to_id,
        reply_to_user_id=reply_to_user_id,
        reply_to_staff_id=reply_to_staff_id
    )
    
    db.add(new_comment)
    post.comments_count += 1 
    
    # Create Notification
    try:
        if notification_recipient_id and notification_recipient_id != student.id:
            # Avoid duplicate notifications? For now, every reply sends one.
            # Clean User Name for message
            # [NEW] Push Notification
            # Fetch recipient object for token
            recipient = await db.get(Student, notification_recipient_id)
            if recipient and recipient.fcm_token:
                title = "💬 Yangi javob"
                # [FIX] Safer username access for Staff
                username = getattr(student, 'username', None) or "foydalanuvchi"
                body = f"@{username} sizning commentingizga javob yozdi"
                await NotificationService.send_push(
                    token=recipient.fcm_token,
                    title=title,
                    body=body,
                    data={"type": "reply", "post_id": str(post_id)}
                )

        await db.commit()
    except Exception as e:
        import traceback
        logger.error(f"--- ERROR in create_comment (Save/Notif): {str(e)} ---\n{traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Izohni saqlashda xato: {str(e)}")

    await db.refresh(new_comment)
    
    # [NEW] Log Activity
    if not is_staff:
        from services.activity_service import ActivityService, ActivityType
        await ActivityService.log_activity(
            db=db,
            user_id=student.id,
            role='student',
            activity_type=ActivityType.COMMENT,
            ref_id=new_comment.id
        )
    
    # Reload for response mapping
    try:
        query = select(ChoyxonaComment).options(
            selectinload(ChoyxonaComment.student),
            selectinload(ChoyxonaComment.reply_to_user), # Eager load reply user
            selectinload(ChoyxonaComment.parent_comment),
            selectinload(ChoyxonaComment.likes), # Required for _map_comment
            selectinload(ChoyxonaComment.post)   # Required for _map_comment (author check)
        ).where(ChoyxonaComment.id == new_comment.id)
        
        result = await db.execute(query)
        new_comment = result.scalar_one()

        # [FIX] Match _map_comment signature (comment, current_user)
        return _map_comment(new_comment, student)
    except Exception as e:
        import traceback
        logger.error(f"--- ERROR in create_comment (Mapping/Response): {str(e)} ---\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Izohni ko'rsatishda xato: {str(e)}")


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponseSchema])
async def get_comments(
    post_id: int,
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comments for a post.
    """
    try:
        from database.models import ChoyxonaComment
        
        post = await db.get(ChoyxonaPost, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post topilmadi")


        # Eager load student, parent, likes, and post (for owner check)
        query = select(ChoyxonaComment).options(
            selectinload(ChoyxonaComment.student),
            selectinload(ChoyxonaComment.staff),
            selectinload(ChoyxonaComment.parent_comment).selectinload(ChoyxonaComment.student),
            selectinload(ChoyxonaComment.parent_comment).selectinload(ChoyxonaComment.staff),
            selectinload(ChoyxonaComment.reply_to_user),
            selectinload(ChoyxonaComment.reply_to_staff),
            selectinload(ChoyxonaComment.post)
        ).where(ChoyxonaComment.post_id == post_id)
        
        result = await db.execute(query)
        all_comments = result.scalars().all()
        
        # Sort by Likes (Desc) then Created Date (Asc)
        all_comments.sort(key=lambda x: (-(x.likes_count or 0), x.created_at))
        
        if not all_comments:
            return []

        # Optimize Access: Batch fetch liked status
        comment_ids = [c.id for c in all_comments]
        is_staff = isinstance(student, Staff)
        liked_ids = set()
        liked_by_author_ids = set()
        
        if comment_ids:
            from database.models import ChoyxonaCommentLike
            
            # 1. Liked by Current User?
            cl_query = select(ChoyxonaCommentLike.comment_id).where(ChoyxonaCommentLike.comment_id.in_(comment_ids))
            if is_staff:
                cl_query = cl_query.where(ChoyxonaCommentLike.staff_id == student.id)
            else:
                cl_query = cl_query.where(ChoyxonaCommentLike.student_id == student.id)
                
            cl_result = await db.execute(cl_query)
            liked_ids = set(cl_result.scalars().all())
            
            # 2. Liked by Post Author? (Hearted)
            pa_sid = post.student_id
            pa_fid = post.staff_id
            
            if pa_sid or pa_fid:
                hla_query = select(ChoyxonaCommentLike.comment_id).where(ChoyxonaCommentLike.comment_id.in_(comment_ids))
                if pa_fid:
                    hla_query = hla_query.where(ChoyxonaCommentLike.staff_id == pa_fid)
                else:
                    hla_query = hla_query.where(ChoyxonaCommentLike.student_id == pa_sid)
                    
                hla_result = await db.execute(hla_query)
                liked_by_author_ids = set(hla_result.scalars().all())

        return [_map_comment_optimized(c, student, c.id in liked_ids, c.id in liked_by_author_ids) for c in all_comments]
    except Exception as e:
        import traceback
        with open("api_debug.log", "a") as f:
            f.write(f"\n--- ERROR {datetime.now()} in get_comments({post_id}) ---\n")
            f.write(traceback.format_exc())
            f.write("-" * 40 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaComment, ChoyxonaCommentLike
    comment = await db.get(ChoyxonaComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Komment topilmadi")

    is_staff = isinstance(student, Staff)
    
    # Check for existing like
    cl_query = select(ChoyxonaCommentLike).where(ChoyxonaCommentLike.comment_id == comment_id)
    if is_staff:
        cl_query = cl_query.where(ChoyxonaCommentLike.staff_id == student.id)
    else:
        cl_query = cl_query.where(ChoyxonaCommentLike.student_id == student.id)
        
    existing_like = await db.scalar(cl_query)
    
    if existing_like:
        await db.delete(existing_like)
        # Atomic Decrement
        comment.likes_count = ChoyxonaComment.likes_count - 1
        liked = False
    else:
        new_like = ChoyxonaCommentLike(
            comment_id=comment_id, 
            student_id=student.id if not is_staff else None,
            staff_id=student.id if is_staff else None
        )
        db.add(new_like)
        # Atomic Increment
        comment.likes_count = ChoyxonaComment.likes_count + 1
        liked = True

    await db.commit()
    # Refresh to get the actual integer value after SQL update
    await db.refresh(comment)
    
    return {"status": "success", "liked": liked, "count": comment.likes_count}

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaComment
    comment = await db.get(ChoyxonaComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Komment topilmadi")
    
    # Allow deletion if:
    # 1. User is the author of the comment
    # 2. User is the author of the POST (admin of thread)
    # But user requirement says: "User faqat o'z kommentini o'chira... olsin"
    # So we strictly check comment author.
    
    # MODERATOR CHECK
    from utils.moderators import is_global_moderator
    login_raw = getattr(student, 'hemis_login', None) or getattr(student, 'hemis_id', None)
    login = str(login_raw or '').strip()
    is_moderator = is_global_moderator(login) or (getattr(student, 'id', 0) == 730)

    if not is_moderator and comment.student_id != student.id and comment.staff_id != student.id:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingizning kommentingizni o'chira olasiz")
        
    
    # Check for replies (Thread integrity)
    # User requested: "komment o'chirilsa u uchun yozilgan javoblar ham o'chirilsin" (Cascade Delete)
    # The DB model has ondelete="SET NULL", so we must manually delete replies to avoid orphans.
    
    # Verify if we should delete replies. Yes per user request.
    # We find all comments that directly reply to this comment ID
    replies = await db.scalars(
        select(ChoyxonaComment).where(ChoyxonaComment.reply_to_comment_id == comment.id)
    )
    replies_list = replies.all()
    
    if replies_list:
        for reply in replies_list:
             # Recursive delete not needed if max depth is 1, but safe to delete direct children.
             # If depth > 1 is added later, we might need recursion, but currently we flat delete replies.
             await db.delete(reply)
             # Update post count for each deleted reply?
             # Yes, if we hard delete a reply, the post loses a comment.
             if comment.post_id:
                 # Note: Currently 'post' object might not be loaded if we didn't eager load it or get it.
                 # We can just decrement post.comments_count by len(replies_list) + 1
                 pass

    # Now delete the main comment
    await db.delete(comment)
    
    # Update Post Comment Count
    if comment.post_id:
        post = await db.get(ChoyxonaPost, comment.post_id)
        if post:
            # Decrement by 1 (the comment itself) + count of deleted replies
            post.comments_count = max(0, post.comments_count - (1 + len(replies_list)))

    await db.commit()
    return {"status": "success", "message": "Komment va uning javoblari o'chirildi"}

@router.put("/comments/{comment_id}", response_model=CommentResponseSchema)
async def edit_comment(
    comment_id: int,
    data: CommentCreateSchema, # Reuse create schema for content
    student: Student = Depends(get_student_or_staff),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaComment
    comment = await db.get(ChoyxonaComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Komment topilmadi")
        
    # MODERATOR CHECK
    from utils.moderators import is_global_moderator
    login_raw = getattr(student, 'hemis_login', None) or getattr(student, 'hemis_id', None)
    login = str(login_raw or '').strip()
    is_moderator = is_global_moderator(login) or (getattr(student, 'id', 0) == 730)

    if not is_moderator and comment.student_id != student.id and comment.staff_id != student.id:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingizning kommentingizni o'zgartira olasiz")
        
    comment.content = data.content
    await db.commit()
    await db.refresh(comment)
    
    # Reload relationships for mapping
    # We need to return the full object for consistent UI updates
    from sqlalchemy.orm import selectinload
    query = select(ChoyxonaComment).options(
        selectinload(ChoyxonaComment.student),
        selectinload(ChoyxonaComment.reply_to_user),
        selectinload(ChoyxonaComment.parent_comment),
        selectinload(ChoyxonaComment.likes),
        selectinload(ChoyxonaComment.post)
    ).where(ChoyxonaComment.id == comment.id)
    
    result = await db.execute(query)
    updated_comment = result.scalar_one()

    return _map_comment(updated_comment, student, student.id)




def _map_comment_optimized(comment: "ChoyxonaComment", current_user, is_liked: bool, is_liked_by_author: bool = False):
    """
    Map ChoyxonaComment model to CommentResponseSchema.
    """
    from api.schemas import CommentResponseSchema
    author = comment.student or comment.staff
    current_user_id = getattr(current_user, 'id', 0)
    is_staff_user = isinstance(current_user, Staff)
    
    # Reply info
    reply_user = None
    reply_content = None
    if comment.parent_comment:
        p_author = comment.parent_comment.student or comment.parent_comment.staff
        reply_user = f"@{p_author.username}" if p_author and getattr(p_author, 'username', None) else (format_name(p_author) if p_author else "Noma'lum")
        reply_content = comment.parent_comment.content[:50] + "..." if len(comment.parent_comment.content) > 50 else comment.parent_comment.content
    elif comment.reply_to_user or comment.reply_to_staff:
         r_author = comment.reply_to_user or comment.reply_to_staff
         reply_user = f"@{getattr(r_author, 'username', None)}" if getattr(r_author, 'username', None) else format_name(r_author)
    
    # MODERATOR CHECK
    from utils.moderators import is_global_moderator
    login_raw = getattr(current_user, 'hemis_login', None) or getattr(current_user, 'hemis_id', None)
    login = str(login_raw or '').strip()
    is_moderator = is_global_moderator(login) or (current_user_id == 730)

    is_mine = False
    if is_moderator:
        is_mine = True
    elif comment.staff_id and is_staff_user and comment.staff_id == current_user_id:
        is_mine = True
    elif comment.student_id and not is_staff_user and comment.student_id == current_user_id:
        is_mine = True

    return CommentResponseSchema(
        id=comment.id,
        post_id=comment.post_id,
        content=comment.content,
        author_id=author.id if author else 0,
        author_name=format_name(author) if author else "Noma'lum",
        author_username=getattr(author, 'username', None),
        author_avatar=getattr(author, 'image_url', None),
        author_image=getattr(author, 'image_url', None),
        image=getattr(author, 'image_url', None),
        author_role=(getattr(author, 'hemis_role', None) or getattr(author, 'role', 'student')) if author else "student",
        author_is_premium=getattr(author, 'is_premium', False) if author else False,
        author_custom_badge=getattr(author, 'custom_badge', None) if author else None,
        created_at=comment.created_at,
        likes_count=comment.likes_count or 0,
        is_liked=is_liked,
        is_liked_by_author=is_liked_by_author,
        is_mine=is_mine,
        reply_to_comment_id=comment.reply_to_comment_id,
        reply_to_username=reply_user,
        reply_to_content=reply_content
    )

def _map_comment(comment: "ChoyxonaComment", current_user):
    # Fallback
    is_liked = False
    current_user_id = getattr(current_user, 'id', 0)
    is_staff = isinstance(current_user, Staff)
    
    if comment.likes:
        if is_staff:
             is_liked = any(l.staff_id == current_user_id for l in comment.likes)
        else:
             is_liked = any(l.student_id == current_user_id for l in comment.likes)
             
    return _map_comment_optimized(comment, current_user, is_liked)
