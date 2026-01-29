from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List

from database.db_connect import AsyncSessionLocal
from database.models import Student, ChoyxonaPost, ChoyxonaPostLike, ChoyxonaPostRepost, ChoyxonaComment
from api.dependencies import get_current_student, get_db
from utils.student_utils import format_name
from api.dependencies import get_current_student, get_db
from api.schemas import PostCreateSchema, PostResponseSchema, CommentCreateSchema, CommentResponseSchema
from services.notification_service import NotificationService

router = APIRouter()

@router.post("/posts", response_model=PostResponseSchema)
async def create_post(
    data: PostCreateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post with strict context binding.
    """
    # 1. Determine Context based on Category
    target_uni = student.university_id
    target_fac = None
    target_spec = None
    
    category = data.category_type
    
    if category == 'university':
        target_uni = student.university_id
        
    elif category == 'faculty':
        target_uni = student.university_id
        target_fac = student.faculty_id
        if not target_fac:
            raise HTTPException(status_code=400, detail="Sizda fakultet biriktirilmagan")
            
    elif category == 'specialty':
        target_uni = student.university_id
        target_fac = student.faculty_id
        target_spec = student.specialty_name
        if not target_spec:
             raise HTTPException(status_code=400, detail="Sizda mutaxassislik (yo'nalish) ma'lumoti yo'q")
    else:
         raise HTTPException(status_code=400, detail="Noto'g'ri kategoriya")
    
    # 2. Create Post
    new_post = ChoyxonaPost(
        student_id=student.id,
        content=data.content,
        category_type=category,
        target_university_id=target_uni,
        target_faculty_id=target_fac,
        target_specialty_name=target_spec
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    # Re-fetch with author to map response
    # Or just use the student object we have
    # Manually construct response to avoid lazy loading 'likes' on async session
    return PostResponseSchema(
        id=new_post.id,
        content=new_post.content,
        category_type=new_post.category_type,
        author_id=student.id, # Fixed: Missing field
        author_name=student.full_name if student.full_name else "Talaba",
        author_username=student.username, # Also add username for consistency
        author_avatar=student.image_url, # Also add avatar for consistency
        author_role="Talaba",
        created_at=new_post.created_at,
        target_university_id=new_post.target_university_id,
        target_faculty_id=new_post.target_faculty_id,
        target_specialty_name=new_post.target_specialty_name,
        likes_count=0,
        is_liked_by_me=False,
        author_is_premium=student.is_premium, # NEW
        author_custom_badge=student.custom_badge # NEW
    )

@router.get("/posts", response_model=List[PostResponseSchema])
async def get_posts(
    category: str = Query(..., description="university, faculty, specialty"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get posts with strict access control filtering.
    """
    # Eager load student for author details
    # Eager load likes and reposts ONLY for determining "is_liked_by_me/is_reposted_by_me" status
    # We DO NOT need to load all comments/likes to count them anymore.
    
    query = select(ChoyxonaPost).options(
        selectinload(ChoyxonaPost.student), 
        selectinload(ChoyxonaPost.likes), 
        selectinload(ChoyxonaPost.reposts)
    ).order_by(desc(ChoyxonaPost.created_at))
    
    # ... (filters remain same) ...
    # 1. Category Filter (Tab Filter)
    query = query.where(ChoyxonaPost.category_type == category)
    
    if category == 'university': 
         query = query.where(ChoyxonaPost.target_university_id == student.university_id)
    elif category == 'faculty':
         query = query.where(
             ChoyxonaPost.target_university_id == student.university_id,
             ChoyxonaPost.target_faculty_id == student.faculty_id
         )
    elif category == 'specialty':
         query = query.where(
             ChoyxonaPost.target_university_id == student.university_id,
             ChoyxonaPost.target_faculty_id == student.faculty_id,
             ChoyxonaPost.target_specialty_name == student.specialty_name
         )
         
    query = query.offset(skip).limit(limit)
        
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return [_map_post(p, p.student, student.id) for p in posts]

@router.get("/posts/reposted", response_model=List[PostResponseSchema])
async def get_reposted_posts(
    target_student_id: int = Query(..., description="Student ID whose reposts we want"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get posts reposted by a specific student.
    """
    # Join Reposts -> Posts -> Student (Author) -> Likes/Reposts
    stmt = select(ChoyxonaPost).join(ChoyxonaPostRepost).options(
        selectinload(ChoyxonaPost.student), # Fix MissingGreenlet
        selectinload(ChoyxonaPost.likes),
        selectinload(ChoyxonaPost.reposts)
    ).where(ChoyxonaPostRepost.student_id == target_student_id).order_by(desc(ChoyxonaPostRepost.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    posts = result.scalars().all()
    
    return [_map_post(p, p.student, student.id) for p in posts]

def format_name(student: Student):
    if not student: return "Unknown"
    
    # We want "First Last" for community posts as requested
    # Database full_name is stored as "Last First [Patronymic]"
    
    f_name = (student.full_name or "").strip()
    if f_name and len(f_name.split()) >= 2:
        parts = f_name.split()
        # parts[0] is Last, parts[1] is First
        # Return "First Last"
        return f"{parts[1]} {parts[0]}".title()
    
    # Fallback to short_name
    s_name = (student.short_name or "").strip()
    if f_name: return f_name.title()
    if s_name: return s_name.title()
    
    return "Talaba"

def _map_post(post: ChoyxonaPost, author: Student, current_user_id: int):
    # Use stored counts
    is_liked = any(l.student_id == current_user_id for l in post.likes) if post.likes else False
    is_reposted = any(r.student_id == current_user_id for r in post.reposts) if post.reposts else False

    return PostResponseSchema(
        id=post.id,
        content=post.content,
        category_type=post.category_type,
        author_id=author.id if author else 0, # NEW
        author_name=format_name(author) if author else "Unknown",
        author_username=author.username if author else None,
        author_avatar=author.image_url,
        author_image=author.image_url, # FALLBACK
        image=author.image_url,        # FALLBACK
        author_role=(author.hemis_role or "student") if author else "student",
        author_is_premium=author.is_premium if author else False, # NEW
        author_custom_badge=author.custom_badge if author else None, # NEW
        created_at=post.created_at,
        target_university_id=post.target_university_id,
        target_faculty_id=post.target_faculty_id,
        target_specialty_name=post.target_specialty_name,
        
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        reposts_count=post.reposts_count,
        
        is_liked_by_me=is_liked,
        is_reposted_by_me=is_reposted,
        is_mine=(post.student_id == current_user_id)
    )
    
@router.get("/posts/{post_id}", response_model=PostResponseSchema)
async def get_post_by_id(
    post_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    query = select(ChoyxonaPost).options(
        selectinload(ChoyxonaPost.student), 
        selectinload(ChoyxonaPost.likes),
        selectinload(ChoyxonaPost.reposts)
    ).where(ChoyxonaPost.id == post_id)
    
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
        
    return _map_post(post, post.student, student.id)

@router.put("/posts/{post_id}", response_model=PostResponseSchema)
async def update_post(
    post_id: int,
    data: PostCreateSchema, # Reuse create schema (content + category)
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Eager load relationships to prevent 500 error during mapping
    query = select(ChoyxonaPost).options(
        selectinload(ChoyxonaPost.likes),
        selectinload(ChoyxonaPost.reposts)
    ).where(ChoyxonaPost.id == post_id)
    
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
        
    if post.student_id != student.id:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingizning postingizni o'zgartira olasiz")
        
    post.content = data.content
    # We generally don't allow changing category/context after creation, but content yes.
    
    await db.commit()
    await db.refresh(post)
    
    # We need to manually load relationships or just return mapped with empty lists if we know they didn't change count-wise
    # But better to just re-fetch fully if needed. For speed, assume 0 for response or existing.
    # Simple fix: return mapped with current user
    return _map_post(post, student, student.id)

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
        
    if post.student_id != student.id:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingizning postingizni o'chira olasiz")
        
    await db.delete(post)
    await db.commit()
    return {"status": "success", "message": "Post o'chirildi"}

@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Check if post exists
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")

    # Check for existing like
    existing_like = await db.scalar(select(ChoyxonaPostLike).where(ChoyxonaPostLike.post_id == post_id, ChoyxonaPostLike.student_id == student.id))
    
    if existing_like:
        await db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1) # Atomic-ish in app logic, better to use SQL expression if high concurrency, but OK for now
        liked = False
    else:
        new_like = ChoyxonaPostLike(post_id=post_id, student_id=student.id)
        db.add(new_like)
        post.likes_count += 1
        liked = True

    await db.commit()
    return {"status": "success", "liked": liked, "count": post.likes_count}

@router.post("/posts/{post_id}/repost")
async def toggle_repost(
    post_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaPostRepost
    # Check if post exists
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")

    # Check for existing repost
    existing_repost = await db.scalar(select(ChoyxonaPostRepost).where(ChoyxonaPostRepost.post_id == post_id, ChoyxonaPostRepost.student_id == student.id))
    
    if existing_repost:
        await db.delete(existing_repost)
        post.reposts_count = max(0, post.reposts_count - 1)
        reposted = False
    else:
        new_repost = ChoyxonaPostRepost(post_id=post_id, student_id=student.id)
        db.add(new_repost)
        post.reposts_count += 1
        reposted = True

    await db.commit()
    return {"status": "success", "reposted": reposted, "count": post.reposts_count}

@router.post("/posts/{post_id}/comments", response_model=CommentResponseSchema)
async def create_comment(
    post_id: int,
    data: CommentCreateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # ... (same checks)
    # 1. Fetch Post to verify access logic
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")
    
    # ... (access checks)
    # 2. Verify Access (User must have same context as post)
    if post.category_type == 'university' and post.target_university_id != student.university_id:
        raise HTTPException(status_code=403, detail="Siz bu universitet postiga yozolmaysiz")
    
    if post.category_type == 'faculty' and (post.target_university_id != student.university_id or post.target_faculty_id != student.faculty_id):
        raise HTTPException(status_code=403, detail="Siz bu fakultet postiga yozolmaysiz")
        
    if post.category_type == 'specialty' and (post.target_specialty_name != student.specialty_name):
         raise HTTPException(status_code=403, detail="Siz bu yo'nalish postiga yozolmaysiz")

    # 3. Create Comment Logic with Depth Control & Notifications
    from database.models import ChoyxonaComment, Notification
    
    final_reply_to_id = data.reply_to_comment_id
    reply_to_user_id = None
    notification_recipient_id = None
    
    if final_reply_to_id:
        parent_comment = await db.get(ChoyxonaComment, final_reply_to_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Javob berilayotgan komment topilmadi")
        
        # Depth Logic: Max 2 levels (Root -> Reply)
        # If parent implies it IS a reply (has parent), we use ITS parent as root.
        # UPDATE: User requested deep context. We keep the Immediate Parent.
        # if parent_comment.reply_to_comment_id is not None:
        #      final_reply_to_id = parent_comment.reply_to_comment_id
        
        # Track who we are effectively replying to (The user who wrote the comment we clicked on)
        reply_to_user_id = parent_comment.student_id
        notification_recipient_id = parent_comment.student_id

    new_comment = ChoyxonaComment(
        post_id=post_id,
        student_id=student.id,
        content=data.content,
        reply_to_comment_id=final_reply_to_id,
        reply_to_user_id=reply_to_user_id
    )
    
    db.add(new_comment)
    post.comments_count += 1 
    
    # Create Notification
    if notification_recipient_id and notification_recipient_id != student.id:
        # Avoid duplicate notifications? For now, every reply sends one.
        # Clean User Name for message
        sender_name = format_name(student.full_name) # Ensure format_name is available or use student.short_name
        
        db.add(notify)
        
        # [NEW] Push Notification
        # Fetch recipient object for token
        recipient = await db.get(Student, notification_recipient_id)
        if recipient and recipient.fcm_token:
            title = "💬 Yangi javob"
            body = f"@{student.username or 'student'} sizning commentingizga javob yozdi"
            await NotificationService.send_push(
                token=recipient.fcm_token,
                title=title,
                body=body,
                data={"type": "reply", "post_id": str(post_id)}
            )

    await db.commit()
    await db.refresh(new_comment)
    
    # Reload for response mapping
    query = select(ChoyxonaComment).options(
        selectinload(ChoyxonaComment.student),
        selectinload(ChoyxonaComment.reply_to_user), # Eager load reply user
        selectinload(ChoyxonaComment.parent_comment),
        selectinload(ChoyxonaComment.likes), # Required for _map_comment
        selectinload(ChoyxonaComment.post)   # Required for _map_comment (author check)
    ).where(ChoyxonaComment.id == new_comment.id)
    
    result = await db.execute(query)
    new_comment = result.scalar_one()

    return _map_comment(new_comment, new_comment.student, student.id)


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponseSchema])
async def get_comments(
    post_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comments for a post.
    """
    from database.models import ChoyxonaComment
    
    post = await db.get(ChoyxonaPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post topilmadi")

    # Eager load student, parent, likes, and post (for owner check)
    # Eager load student, parent, likes, and post (for owner check)
    query = select(ChoyxonaComment).options(
        selectinload(ChoyxonaComment.student),
        selectinload(ChoyxonaComment.parent_comment).selectinload(ChoyxonaComment.student),
        selectinload(ChoyxonaComment.likes),
        selectinload(ChoyxonaComment.post)
    ).where(ChoyxonaComment.post_id == post_id)
    
    result = await db.execute(query)
    all_comments = result.scalars().all()
    
    
    # Logic Change (2026-01-23):
    # Previous logic only handled 1 level of replies (Parent -> Reply). 
    # Any Level 2 reply (Reply to Reply) was being dropped because it wasn't in replies_map[RootID].
    # 
    # Since Frontend now handles recursive grouping ("findRootId"), we can simply return ALL comments.
    # We should sort them logically (Created Date) so frontend processes them in order.
    
    # Sort all by created_at (ascending) so threads build naturally?
    # Or just returning them flat is enough.
    
    # Sort by Likes (Desc) then Created Date (Asc)
    # Most popular first, then oldest to newest for equal likes
    all_comments.sort(key=lambda x: (-x.likes_count, x.created_at))
    
    # We can still prioritize Roots if we want stable initial load??
    # Actually, sorting by date is safest. But maybe Roots by Likes first?
    # No, simple is better. Return all.
    
    final_list = all_comments
    print(f"DEBUG: Returning {len(final_list)} comments for post {post_id}")
    return [_map_comment(c, c.student, student.id) for c in final_list]

@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaComment, ChoyxonaCommentLike
    comment = await db.get(ChoyxonaComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Komment topilmadi")

    existing_like = await db.scalar(select(ChoyxonaCommentLike).where(ChoyxonaCommentLike.comment_id == comment_id, ChoyxonaCommentLike.student_id == student.id))
    
    if existing_like:
        await db.delete(existing_like)
        # Atomic Decrement
        comment.likes_count = ChoyxonaComment.likes_count - 1
        liked = False
    else:
        new_like = ChoyxonaCommentLike(comment_id=comment_id, student_id=student.id)
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
    student: Student = Depends(get_current_student),
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
    
    if comment.student_id != student.id:
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
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ChoyxonaComment
    comment = await db.get(ChoyxonaComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Komment topilmadi")
        
    if comment.student_id != student.id:
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



def _map_comment(comment: "ChoyxonaComment", author: Student, current_user_id: int):
    from api.schemas import CommentResponseSchema
    
    reply_user = None
    reply_content = None
    
    if comment.reply_to_user:
        # Priority 1: Specific User we replied to (New Logic)
        reply_user = f"@{comment.reply_to_user.username}" if comment.reply_to_user.username else format_name(comment.reply_to_user.full_name)
        if comment.parent_comment:
             reply_content = comment.parent_comment.content
    elif comment.parent_comment:
        # Priority 2: Fallback (Old Logic)
        reply_user = format_name(comment.parent_comment.student.full_name) if comment.parent_comment.student else "Noma'lum"
        reply_content = comment.parent_comment.content

    # Determine if liked by me
    # If loaded eagerly:
    is_liked = any(l.student_id == current_user_id for l in comment.likes) if comment.likes else False
    
    # Identify Author role or "Author Like"
    # Logic: is_liked_by_author = True if the POST OWNER liked this comment.
    # To do this, we need post_owner_id. Comment->Post->Student.
    # We should eager load Post to check this.
    # Identify Author role or "Author Like"
    # Logic: is_liked_by_author = True if the POST OWNER liked this comment.
    is_liked_by_author = False
    
    # Safely check if post exists and if we have likes on the comment
    if comment.post and comment.likes:
         is_liked_by_author = any(l.student_id == comment.post.student_id for l in comment.likes)

    return CommentResponseSchema(
        id=comment.id,
        post_id=comment.post_id,
        content=comment.content,
        author_id=author.id if author else 0, # NEW
        author_name=format_name(author.full_name) if author else "Noma'lum",
        author_username=author.username if author else None,
        # DEBUG USERNAME
        # print(f"DEBUG COMMENT {comment.id}: Author={author.full_name if author else 'None'}, Username={author.username if author else 'None'}"), 
        author_avatar=author.image_url,
        author_image=author.image_url, # FALLBACK
        image=author.image_url,        # FALLBACK
        author_role=(author.hemis_role or "student") if author else "student",
        author_is_premium=author.is_premium if author else False, # NEW
        author_custom_badge=author.custom_badge if author else None, # NEW
        created_at=comment.created_at,
        
        likes_count=comment.likes_count,
        is_liked=is_liked,
        is_liked_by_author=is_liked_by_author,
        
        is_mine=(comment.student_id == current_user_id),
        
        reply_to_comment_id=comment.reply_to_comment_id, # NEW
        reply_to_username=reply_user,
        reply_to_content=reply_content
    )
