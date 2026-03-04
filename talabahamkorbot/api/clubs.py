from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from api.dependencies import get_current_student, get_db, get_club_leader
from api.schemas import (
    ClubSchema, ClubMembershipSchema, ClubMemberSchema, 
    ClubAnnouncementSchema, ClubEventSchema, ClubEventParticipantSchema,
    ClubCreateSchema, ClubUpdateSchema
)
from database.models import (
    Student, Club, ClubMembership, ClubAnnouncement, 
    ClubEvent, ClubEventParticipant, University
)

router = APIRouter()

class JoinClubRequest(BaseModel):
    club_id: int

@router.get("/my", response_model=List[ClubMembershipSchema])
async def get_my_clubs(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """List clubs the student has joined."""
    memberships = await db.scalars(
        select(ClubMembership)
        .where(ClubMembership.student_id == student.id)
        .options(selectinload(ClubMembership.club))
    )
    result = []
    for m in memberships.all():
        data = ClubMembershipSchema.from_orm(m)
        is_direct_leader = m.club.leader_student_id == student.id
        is_student_council_admin = (
            getattr(m.club, 'department', '') == 'Student Council' and 
            (getattr(student, 'role', '') == 'student_council' or getattr(student, 'hemis_role', '') == 'student_council')
        )
        if is_direct_leader or is_student_council_admin:
            data.club.is_leader = True
            data.role = "leader"
        result.append(data)
    return result

@router.post("/", response_model=ClubSchema)
async def create_club(
    req: ClubCreateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """(Yetakchi) Create a new club for their university."""
    if student.hemis_role != 'yetakchi':
        raise HTTPException(status_code=403, detail="Klub yaratish ruxsati faqat yetakchilar uchun berilgan.")
    
    leader_id = student.id
    if req.leader_login:
        leader_student = await db.scalar(
            select(Student).where(Student.hemis_login == req.leader_login)
        )
        if not leader_student:
            raise HTTPException(status_code=404, detail="Kiritilgan HEMIS login bo'yicha talaba topilmadi.")
        leader_id = leader_student.id

    # Optional logic: create a default icon or color if not provided
    club = Club(
        name=req.name,
        description=req.description,
        department=req.department,
        icon=req.icon or "groups_rounded",
        color=req.color or "#4A90E2",
        statute_link=req.statute_link,
        channel_link=req.channel_link,
        leader_student_id=leader_id
    )
    db.add(club)
    await db.commit()
    await db.refresh(club)
    
    # Actually, setting `leader_student_id` is sufficient for a club leader, 
    # but let's add them as a member too if they aren't already
    membership = ClubMembership(
        student_id=leader_id,
        club_id=club.id
    )
    db.add(membership)
    await db.commit()
    
    return club

@router.get("/all", response_model=List[ClubSchema])
async def get_all_clubs(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """List all available clubs with member counts."""
    from sqlalchemy import func
    
    # Subquery for member counts
    subq = (
        select(ClubMembership.club_id, func.count(ClubMembership.id).label('member_count'))
        .group_by(ClubMembership.club_id)
        .subquery()
    )
    
    # Subquery for current user's memberships
    my_subq = (
        select(ClubMembership.club_id)
        .where(ClubMembership.student_id == student.id)
        .subquery()
    )
    
    query = (
        select(
            Club, 
            func.coalesce(subq.c.member_count, 0).label('members_count'),
            (my_subq.c.club_id != None).label('is_joined')
        )
        .outerjoin(subq, Club.id == subq.c.club_id)
        .outerjoin(my_subq, Club.id == my_subq.c.club_id)
    )
    
    result = await db.execute(query)
    
    clubs_data = []
    for club, members_count, is_joined in result.all():
        data = ClubSchema.from_orm(club)
        data.members_count = members_count
        data.is_joined = is_joined
        
        is_direct_leader = club.leader_student_id == student.id
        is_student_council_admin = (
            getattr(club, 'department', '') == 'Student Council' and 
            (getattr(student, 'role', '') == 'student_council' or getattr(student, 'hemis_role', '') == 'student_council')
        )
        if is_direct_leader or is_student_council_admin:
            data.is_leader = True
            
        clubs_data.append(data)
        
    return clubs_data

@router.post("/join")
async def join_club(
    req: JoinClubRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a club.
    In a real scenario, we should verify Telegram Channel subscription.
    For now, we trust the client (or verify later).
    """
    # Check if already a member
    existing = await db.scalar(
        select(ClubMembership)
        .where(
            ClubMembership.student_id == student.id,
            ClubMembership.club_id == req.club_id
        )
    )
    if existing:
        return {"status": "already_joined", "message": "Siz allaqachon a'zosiz"}
    
    # Check if club exists
    club = await db.scalar(select(Club).where(Club.id == req.club_id).options(selectinload(Club.leaders)))
    if not club:
         raise HTTPException(status_code=404, detail="Club not found")

    from database.models import TgAccount
    tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == student.id))

    verify_channel_id = club.telegram_channel_id
    if not verify_channel_id and club.channel_link:
        if "t.me/" in club.channel_link and "+" not in club.channel_link:
            handle = club.channel_link.split("t.me/")[-1].strip("/")
            if handle:
                verify_channel_id = f"@{handle}"

    # [NEW] Verify Telegram Channel Subscription
    if verify_channel_id:
        if not tg_acc or not tg_acc.telegram_id:
             return {"status": "error", "message": "Botga start bosmagansiz / Telegram ulanmagan. Ilovangiz Profil yorlig'ida telegram profilni botga bog'lang."}
             
        try:
            from bot import bot
            member = await bot.get_chat_member(verify_channel_id, tg_acc.telegram_id)
            if member.status in ['left', 'kicked']:
                return {"status": "not_subscribed", "channel_link": club.channel_link}
        except Exception as e:
            # Maybe the bot is not admin in the channel, or channel ID is invalid
            print(f"Error checking chat member for {verify_channel_id}: {e}")
            if "chat not found" in str(e).lower() or "bot is not a member" in str(e).lower():
                return {"status": "error", "message": "Kanal topilmadi yoki bot kanal admini emas. Sardor botni kanalga admin qilishi shart."}
            # Or assume they haven't subscribed to be safe
            return {"status": "not_subscribed", "channel_link": club.channel_link}

    membership = ClubMembership(
        student_id=student.id,
        club_id=req.club_id
    )
    db.add(membership)
    await db.commit()
    # --- [NEW] NOTIFY LEADERS ---
    try:
        from bot import bot
        from database.models import TgAccount
        
        # Eager load already happened above
        leader_staff_ids = [l.id for l in club.leaders]
        leader_student_id = club.leader_student_id
        
        # 2. Get Telegram IDs
        recipients = []
        
        # Staff leaders
        if leader_staff_ids:
            staff_accs = await db.scalars(select(TgAccount).where(TgAccount.staff_id.in_(leader_staff_ids)))
            recipients.extend([acc.telegram_id for acc in staff_accs if acc.telegram_id])
            
        # Student leader
        if leader_student_id:
            stud_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == leader_student_id))
            if stud_acc and stud_acc.telegram_id:
                recipients.append(stud_acc.telegram_id)
        
        # 3. Send Notifications
        unique_recipients = list(set(recipients))
        
        msg_text = (
            f"🔔 <b>Yangi a'zo!</b>\n\n"
            f"To'garak: <b>{club.name}</b>\n"
            f"Talaba: {student.full_name}\n"
            f"Guruh: {student.group_number or 'Aniqlanmagan'}"
        )
        
        for tid in unique_recipients:
            try:
                await bot.send_message(tid, msg_text, parse_mode="HTML")
            except Exception as e:
                print(f"Failed to notify leader {tid}: {e}")
                
    except Exception as e:
        # Don't fail the join process if notification fails
        print(f"Global notification error: {e}")
        pass
    # ----------------------------
    
    return {"status": "success"}

@router.get("/{club_id}/members", response_model=List[ClubMemberSchema])
async def get_club_members(
    club_id: int,
    club: Club = Depends(get_club_leader),
    db: AsyncSession = Depends(get_db)
):
    """(Leader) Get all members of a club."""
    from sqlalchemy.orm import joinedload
    
    memberships = await db.execute(
        select(ClubMembership)
        .where(ClubMembership.club_id == club_id)
        .options(joinedload(ClubMembership.student))
    )
    
    ms = memberships.scalars().all()
    res = []
    for m in ms:
        # Use the string property directly instead of relationship to avoid N+1 and Detached issues
        faculty_name = m.student.faculty_name or (m.student.faculty.name if getattr(m.student, 'faculty', None) else None)
        
        # Try to find telegram username from TgAccount
        # Telegram username fallback
        username = getattr(m.student, 'username', None)
        res.append({
            "student_id": m.student_id,
            "full_name": m.student.full_name,
            "faculty_name": faculty_name,
            "group_number": m.student.group_number,
            "telegram_username": username,
            "joined_at": m.joined_at,
            "status": getattr(m, 'status', 'active'),
            "image_url": m.student.image_url
        })
    return res


@router.get("/{club_id}/members/{student_id}")
async def get_club_member_profile(
    club_id: int,
    student_id: int,
    club: Club = Depends(get_club_leader),
    db: AsyncSession = Depends(get_db)
):
    """(Leader) Get a member's club profile and their activities within this club."""
    from sqlalchemy.orm import joinedload
    
    # 1. Get member basic info
    membership = await db.scalar(
        select(ClubMembership)
        .where(
            ClubMembership.club_id == club_id,
            ClubMembership.student_id == student_id
        )
        .options(joinedload(ClubMembership.student))
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found.")
        
    faculty_name = membership.student.faculty_name or (membership.student.faculty.name if getattr(membership.student, 'faculty', None) else None)
    
    # 2. Get their activities (events attended) in this club
    # Find all events in this club where this student participated and attended
    part_query = await db.scalars(
        select(ClubEventParticipant)
        .join(ClubEvent, ClubEvent.id == ClubEventParticipant.event_id)
        .where(
            ClubEvent.club_id == club_id,
            ClubEventParticipant.student_id == student_id,
            ClubEventParticipant.attendance_status == 'attended'
        )
        .options(joinedload(ClubEventParticipant.event))
    )
    
    activities = []
    for part in part_query.all():
        activities.append({
            "event_title": part.event.title,
            "event_date": part.event.event_date.isoformat() if part.event.event_date else None,
            "status": "attended"
        })
        
    return {
        "student_id": membership.student_id,
        "full_name": membership.student.full_name,
        "faculty_name": faculty_name,
        "group_number": membership.student.group_number,
        "joined_at": membership.joined_at,
        "image_url": membership.student.image_url,
        "activities": activities
    }


@router.delete("/{club_id}/members/{student_id}")
async def remove_club_member(
    club_id: int,
    student_id: int,
    club: Club = Depends(get_club_leader),
    db: AsyncSession = Depends(get_db)
):
    """(Leader) Remove a student from the club."""
    membership = await db.scalar(
        select(ClubMembership)
        .where(
            ClubMembership.club_id == club_id,
            ClubMembership.student_id == student_id
        )
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found.")
        
    from database.models import TgAccount
    telegram_id = membership.telegram_id
    if not telegram_id:
        tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == student_id))
        if tg_acc:
            telegram_id = str(tg_acc.telegram_id)
            
    if telegram_id and club.telegram_channel_id:
        from bot import bot
        import logging
        try:
            # Kick user and unban to allow future joining
            await bot.ban_chat_member(chat_id=club.telegram_channel_id, user_id=int(telegram_id))
            await bot.unban_chat_member(chat_id=club.telegram_channel_id, user_id=int(telegram_id))
        except Exception as e:
            logging.error(f"Error kicking user {telegram_id} from {club.telegram_channel_id}: {e}")

    await db.delete(membership)
    await db.commit()
    return {"status": "success", "message": "Talaba klub a'zolari safidan chiqarildi"}

class AnnouncementCreateSchema(BaseModel):
    content: str
    media_url: Optional[str] = None
    send_to_telegram: bool = False

@router.post("/{club_id}/announcements")
async def create_club_announcement(
    club_id: int,
    req: AnnouncementCreateSchema,
    student: Student = Depends(get_current_student),
    club: Club = Depends(get_club_leader),
    db: AsyncSession = Depends(get_db)
):
    """(Leader) Create announcement, optionally send to Telegram."""
    ann = ClubAnnouncement(
        club_id=club_id,
        created_by=student.id,
        content=req.content,
        media_url=req.media_url
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    
    # Send to TG logic
    if req.send_to_telegram and getattr(club, 'telegram_channel_id', None):
        try:
            from bot import bot
            channel_id = club.telegram_channel_id
            
            # Very basic handling (in real scenario handled properly)
            msg = f"<b>📣 YANGLIK:</b>\n\n{req.content}"
            if req.media_url:
                await bot.send_photo(channel_id, req.media_url, caption=msg, parse_mode="HTML")
            else:
                await bot.send_message(channel_id, msg, parse_mode="HTML")
        except Exception as e:
            print(f"Failed to post to telegram channel: {e}")
            
    return {"status": "success", "id": ann.id}

@router.get("/{club_id}/announcements", response_model=List[ClubAnnouncementSchema])
async def get_club_announcements(
    club_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get announcements for a club."""
    from sqlalchemy import desc
    anns = await db.scalars(
        select(ClubAnnouncement)
        .where(ClubAnnouncement.club_id == club_id)
        .order_by(desc(ClubAnnouncement.created_at))
        .options(selectinload(ClubAnnouncement.author))
        .limit(50)
    )
    
    res = []
    for a in anns.all():
        data = ClubAnnouncementSchema.from_orm(a)
        if a.author:
            data.author_name = a.author.full_name
        res.append(data)
    return res

class EventCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: str # ISO format

@router.post("/{club_id}/events")
async def create_club_event(
    club_id: int,
    req: EventCreateSchema,
    student: Student = Depends(get_current_student),
    club: Club = Depends(get_club_leader),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    dt = datetime.fromisoformat(req.event_date.replace("Z", "+00:00"))
    
    ev = ClubEvent(
        club_id=club_id,
        title=req.title,
        description=req.description,
        location=req.location,
        event_date=dt,
        created_by=student.id
    )
    db.add(ev)
    await db.commit()
    return {"status": "success", "id": ev.id}

@router.get("/{club_id}/events", response_model=List[ClubEventSchema])
async def get_club_events(
    club_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import desc, func
    from sqlalchemy.orm import selectinload
    
    evs = await db.scalars(
        select(ClubEvent)
        .options(selectinload(ClubEvent.images))
        .where(ClubEvent.club_id == club_id)
        .order_by(desc(ClubEvent.event_date))
    )
    
    res = []
    events_list = evs.all()
    if events_list:
        event_ids = [e.id for e in events_list]
        
        # Get pariticpants counts
        c_subq = await db.execute(
            select(
                ClubEventParticipant.event_id,
                func.count(ClubEventParticipant.id)
            )
            .where(ClubEventParticipant.event_id.in_(event_ids))
            .group_by(ClubEventParticipant.event_id)
        )
        counts = {row[0]: row[1] for row in c_subq.all()}
        
        # Get my participations
        m_subq = await db.scalars(
            select(ClubEventParticipant.event_id)
            .where(
                ClubEventParticipant.event_id.in_(event_ids),
                ClubEventParticipant.student_id == student.id
            )
        )
        my_part_ids = set(m_subq.all())
        
        from datetime import datetime
        now_dt = datetime.utcnow()
        for e in events_list:
            schema = ClubEventSchema.from_orm(e)
            schema.participants_count = counts.get(e.id, 0)
            schema.is_participating = e.id in my_part_ids
            schema.status = "O'tkazildi" if e.event_date < now_dt else "O'tkaziladi"
            schema.images = e.images if hasattr(e, 'images') else []
            res.append(schema)
            
    return res

@router.post("/events/{event_id}/participate")
async def participate_club_event(
    event_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    ev = await db.get(ClubEvent, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
        
    part = await db.scalar(
        select(ClubEventParticipant)
        .where(
            ClubEventParticipant.event_id == event_id,
            ClubEventParticipant.student_id == student.id
        )
    )
    if part:
        # Unsubscribe if already participating
        await db.delete(part)
        await db.commit()
        return {"status": "success", "action": "removed"}
        
    # Subscribe
    part = ClubEventParticipant(
        event_id=event_id,
        student_id=student.id
    )
    db.add(part)
    await db.commit()
    return {"status": "success", "action": "added"}

@router.get("/events/{event_id}/participants", response_model=List[ClubEventParticipantSchema])
async def get_event_participants(
    event_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Verify leader scope
    ev = await db.get(ClubEvent, event_id)
    if not ev:
         raise HTTPException(status_code=404, detail="Event not found")
         
    club = await get_club_leader(ev.club_id, student, db)
        
    from sqlalchemy.orm import joinedload
    memberships = await db.scalars(
        select(ClubMembership)
        .where(ClubMembership.club_id == ev.club_id)
        .options(joinedload(ClubMembership.student))
    )
    all_members = memberships.all()
    
    parts = await db.scalars(
        select(ClubEventParticipant)
        .where(ClubEventParticipant.event_id == event_id)
    )
    part_map = {p.student_id: p for p in parts.all()}
    
    res = []
    for m in all_members:
        faculty_name = m.student.faculty_name or (m.student.faculty.name if getattr(m.student, 'faculty', None) else None)
        p = part_map.get(m.student_id)
        
        # registered, attended, missed, not_registered
        status = p.attendance_status if p else "not_registered"
        res.append({
            "student_id": m.student_id,
            "full_name": m.student.full_name,
            "faculty_name": faculty_name,
            "group_number": m.student.group_number,
            "attendance_status": status,
            "image_url": m.student.image_url
        })
    return res

class AttendanceUpdateSchema(BaseModel):
    student_id: int
    attendance_status: str # "attended" or "missed" or "registered"

@router.post("/events/{event_id}/attendance")
async def update_event_attendance(
    event_id: int,
    req: AttendanceUpdateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Verify leader scope
    ev = await db.get(ClubEvent, event_id)
    if not ev:
         raise HTTPException(status_code=404, detail="Event not found")
         
    club = await get_club_leader(ev.club_id, student, db)
        
    part = await db.scalar(
        select(ClubEventParticipant)
        .where(ClubEventParticipant.event_id == event_id, ClubEventParticipant.student_id == req.student_id)
    )
    
    if not part:
        # If not manually registered, auto-register them
        part = ClubEventParticipant(
            event_id=event_id,
            student_id=req.student_id,
            attendance_status=req.attendance_status
        )
        db.add(part)
    else:
        part.attendance_status = req.attendance_status
        
    await db.commit()
    return {"status": "success", "attendance_status": part.attendance_status}

@router.post("/events/{event_id}/complete_activity")
async def complete_event_activity(
    event_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    from database.models import ClubEventParticipant, UserActivity, UserActivityImage, ClubEventImage, ClubEvent
    from datetime import datetime

    ev = await db.get(ClubEvent, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
        
    parts = await db.scalars(
        select(ClubEventParticipant)
        .where(
            ClubEventParticipant.event_id == event_id,
            ClubEventParticipant.attendance_status == "attended"
        )
    )
    parts_list = parts.all()
    
    if not parts_list:
        ev.is_processed = True
        await db.commit()
        return {"success": True, "message": "No attended participants"}
        
    # Get uploaded photos
    photos = await db.scalars(select(ClubEventImage).where(ClubEventImage.event_id == event_id))
    photos_list = photos.all()
    
    created_count = 0
    for p in parts_list:
        existing = await db.scalar(
            select(UserActivity).where(
                UserActivity.student_id == p.student_id,
                UserActivity.name == ev.title[:255],
                UserActivity.category == "togarak"
            )
        )
        if existing:
            continue
            
        desc = ev.description or ''
        activity = UserActivity(
            student_id=p.student_id,
            category="togarak",
            name=ev.title[:255],
            description=f"Klub tadbirida faol ishtirok etildi. {desc[:100]}",
            date=ev.event_date.strftime("%Y-%m-%d") if ev.event_date else datetime.utcnow().strftime("%Y-%m-%d"),
            status="approved"
        )
        db.add(activity)
        await db.flush() # get ID
        
        for img in photos_list:
            u_img = UserActivityImage(
                activity_id=activity.id,
                file_id=img.file_id
            )
            db.add(u_img)
        created_count += 1
        
    if created_count > 0:
        ev.is_processed = True
        await db.commit()
        return {"success": True, "created": created_count}
    else:
        ev.is_processed = True
        await db.commit()
        return {"success": True, "message": "All already recorded"}

@router.put("/{club_id}")
async def update_club(
    club_id: int,
    req: ClubUpdateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    if student.hemis_role != 'yetakchi':
        raise HTTPException(status_code=403, detail="Sizga ruxsat yo'q")
        
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Klub topilmadi")
        
    if req.name is not None:
        club.name = req.name
    if req.department is not None:
        club.department = req.department
    if req.description is not None:
        club.description = req.description
    if req.channel_link is not None:
        club.channel_link = req.channel_link
        
    if req.leader_login is not None:
        leader_student = await db.scalar(
            select(Student).where(Student.hemis_login == req.leader_login)
        )
        if not leader_student:
             raise HTTPException(status_code=404, detail="Sardor (HEMIS login) topilmadi")
             
        club.leader_student_id = leader_student.id
        
        # Optionally add leader to membership if they aren't there
        existing = await db.scalar(
            select(ClubMembership).where(
                ClubMembership.student_id == leader_student.id,
                ClubMembership.club_id == club.id
            )
        )
        if not existing:
             m = ClubMembership(
                 club_id=club.id,
                 student_id=leader_student.id,
                 status="active"
             )
             db.add(m)
             
    await db.commit()
    await db.refresh(club)
    return {"message": "Muvaffaqiyatli saqlandi"}

@router.delete("/{club_id}")
async def delete_club(
    club_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """(Yetakchi) Delete a club permanently."""
    if student.hemis_role != 'yetakchi':
        raise HTTPException(status_code=403, detail="Sizga ruxsat yo'q (Faqat yetakchilar uchun)")
        
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Klub topilmadi")
        
    await db.delete(club)
    await db.commit()
    return {"message": "Klub o'chirildi", "status": "success"}
