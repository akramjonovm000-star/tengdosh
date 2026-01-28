from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, and_, func
from database.db_connect import AsyncSessionLocal
from database.models import Student, PrivateChat, PrivateMessage, StudentNotification
from api.dependencies import get_current_student, get_db
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_or_create_chat(user1_id: int, user2_id: int, db: AsyncSession):
    # Ensure consistent ordering to avoid duplicates (min_id, max_id)
    u1, u2 = min(user1_id, user2_id), max(user1_id, user2_id)
    
    # Check existing
    query = select(PrivateChat).where(
        PrivateChat.user1_id == u1,
        PrivateChat.user2_id == u2
    )
    result = await db.execute(query)
    chat = result.scalar_one_or_none()
    
    if not chat:
        chat = PrivateChat(user1_id=u1, user2_id=u2)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
    return chat

@router.post("/start/{target_user_id}")
async def start_chat(
    target_user_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    if target_user_id == student.id:
        raise HTTPException(status_code=400, detail="O'zingiz bilan chat qura olmaysiz")
        
    target = await db.get(Student, target_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        
    chat = await get_or_create_chat(student.id, target_user_id, db)
    return {"chat_id": chat.id, "target_user": {"id": target.id, "full_name": target.full_name, "image_url": target.image_url, "username": target.username, "custom_badge": target.custom_badge}}

@router.get("/list")
async def list_chats(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """List all chats ordered by last activity"""
    from sqlalchemy.orm import selectinload
    
    query = select(PrivateChat).options(
        selectinload(PrivateChat.user1),
        selectinload(PrivateChat.user2)
    ).where(
        or_(PrivateChat.user1_id == student.id, PrivateChat.user2_id == student.id)
    ).order_by(desc(PrivateChat.last_message_time))
    
    result = await db.execute(query)
    chats = result.scalars().all()
    
    response = []
    for c in chats:
        other_user = c.user2 if c.user1_id == student.id else c.user1
        unread = c.user1_unread_count if c.user1_id == student.id else c.user2_unread_count
        
        # Determine who sent the last message
        # We query the actual last message to be precise
        last_msg_stmt = select(PrivateMessage).where(PrivateMessage.chat_id == c.id).order_by(desc(PrivateMessage.created_at)).limit(1)
        last_msg_res = await db.execute(last_msg_stmt)
        last_msg = last_msg_res.scalar_one_or_none()
        
        last_sender_id = last_msg.sender_id if last_msg else 0
        is_last_mine = (last_sender_id == student.id)
        
        response.append({
            "id": c.id,
            "target_user": {
                "id": other_user.id,
                "full_name": other_user.full_name,
                "image_url": other_user.image_url,
                "username": other_user.username,
                "role": other_user.hemis_role or "student",
                "custom_badge": other_user.custom_badge
            },
            "last_message": c.last_message_content,
            "last_message_time": c.last_message_time,
            "unread_count": unread,
            "is_last_message_mine": is_last_mine # NEW FIELD
        })
        
    return response

@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: int,
    before_id: int = Query(None),
    limit: int = 50,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Verify access
    chat = await db.get(PrivateChat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
        
    if chat.user1_id != student.id and chat.user2_id != student.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        
    # Mark as read
    if chat.user1_id == student.id:
        chat.user1_unread_count = 0
    else:
        chat.user2_unread_count = 0
    
    # Query messages
    stmt = select(PrivateMessage).where(PrivateMessage.chat_id == chat_id)
    if before_id:
        stmt = stmt.where(PrivateMessage.id < before_id)
        
    stmt = stmt.order_by(desc(PrivateMessage.created_at)).limit(limit)
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Commit read status
    await db.commit()
    
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "content": m.content,
            "created_at": m.created_at,
            "is_read": m.is_read,
            "is_mine": m.sender_id == student.id
        }
        for m in messages
    ]

@router.post("/{chat_id}/send")
async def send_message(
    chat_id: int,
    data: dict, # {"content": "..."}
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    content = data.get("content")
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Xabar bo'sh bo'lishi mumkin emas")
        
    chat = await db.get(PrivateChat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
        
    if chat.user1_id != student.id and chat.user2_id != student.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        
    # Create Message
    msg = PrivateMessage(
        chat_id=chat_id,
        sender_id=student.id,
        content=content
    )
    db.add(msg)
    
    # Update Chat Meta
    chat.last_message_content = content[:100] # Preview
    chat.last_message_time = datetime.utcnow()
    
    target_id = chat.user2_id if chat.user1_id == student.id else chat.user1_id
    
    if chat.user1_id == target_id:
        chat.user1_unread_count += 1
    else:
        chat.user2_unread_count += 1
        
    await db.commit()
    await db.refresh(msg)
    
    # Send Notification (Lightweight)
    try:
        notif = StudentNotification(
            student_id=target_id,
            title=f"Yangi xabar: {student.full_name}",
            body=content[:50],
            type="message",
            data=str(chat_id) # Link to chat
        )
        db.add(notif)
        await db.commit()
    except Exception as e:
        logger.error(f"Chat Notif Error: {e}")
        
    return {
        "id": msg.id,
        "content": msg.content,
        "created_at": msg.created_at,
        "sender_id": msg.sender_id
    }
