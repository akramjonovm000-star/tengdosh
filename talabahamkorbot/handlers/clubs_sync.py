from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connect import AsyncSessionLocal
from database.models import Club, ClubMembership, TgAccount
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated, bot: Bot):
    """
    Triggers when a user leaves a channel where the bot is admin.
    Marks their club membership as 'inactive' if the channel matches a club.
    """
    channel_id = str(event.chat.id)
    channel_user = f"@{event.chat.username}" if event.chat.username else None
    user_id = event.from_user.id
    
    logger.info(f"User {user_id} left channel {channel_id} ({channel_user})")
    
    async with AsyncSessionLocal() as db:
        # Check if this channel is linked to any club
        from sqlalchemy import or_
        club = await db.scalar(
            select(Club).where(
                or_(
                    Club.telegram_channel_id == channel_id,
                    Club.telegram_channel_id == channel_user
                )
            )
        )
        
        if club:
            # Find the user's student_id using TgAccount
            tg_acc = await db.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id))
            if tg_acc and tg_acc.student_id:
                # Update membership status
                membership = await db.scalar(
                    select(ClubMembership)
                    .where(
                        ClubMembership.club_id == club.id,
                        ClubMembership.student_id == tg_acc.student_id
                    )
                )
                
                if membership and membership.status != "inactive":
                    membership.status = "inactive"
                    await db.commit()
                    logger.info(f"Marked Student {tg_acc.student_id} as inactive in Club {club.id}")

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    """
    Triggers when a user joins a channel where the bot is admin.
    Syncs the telegram_id and optionally marks 'active'.
    """
    channel_id = str(event.chat.id)
    channel_user = f"@{event.chat.username}" if event.chat.username else None
    user_id = event.from_user.id
    
    logger.info(f"User {user_id} joined channel {channel_id} ({channel_user})")
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import or_
        club = await db.scalar(
            select(Club).where(
                or_(
                    Club.telegram_channel_id == channel_id,
                    Club.telegram_channel_id == channel_user
                )
            )
        )
        
        if club:
            tg_acc = await db.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id))
            if tg_acc and tg_acc.student_id:
                membership = await db.scalar(
                    select(ClubMembership)
                    .where(
                        ClubMembership.club_id == club.id,
                        ClubMembership.student_id == tg_acc.student_id
                    )
                )
                
                if membership:
                    if membership.telegram_id != str(user_id) or membership.status != "active":
                        membership.telegram_id = str(user_id)
                        membership.status = "active"
                        await db.commit()
                        logger.info(f"Synced Student {tg_acc.student_id} in Club {club.id} as active")
