import logging
import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, University, Staff, Student

logger = logging.getLogger(__name__)


from datetime import datetime, timedelta

class SubscriptionMiddleware(BaseMiddleware):
    """
    Foydalanuvchi o‘z universitetining majburiy kanaliga a'zo ekanligini tekshiradi.
    Keshlash: 5 daqiqa.
    """
    def __init__(self):
        super().__init__()
        self.cache: Dict[int, Dict[str, Any]] = {} # {user_id: {"status": bool, "expiry": datetime, "channel": str}}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        # 1. Update turini aniqlash (Message yoki CallbackQuery)
        start_time = time.time()
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            # We don't answer immediately to allow handlers to use alert/text
        else:
            return await handler(event, data)

        if not user or user.is_bot:
            res = await handler(event, data)
            if isinstance(event, CallbackQuery):
                try: await event.answer()
                except: pass
            return res
            
        # Is this an automated channel post or a forward from a channel?
        is_channel_post = getattr(event, "sender_chat", None) is not None and getattr(event.sender_chat, "type", "") == "channel"
        is_forwarded_channel = getattr(event, "forward_from_chat", None) is not None and getattr(event.forward_from_chat, "type", "") == "channel"

        # Check Global Channel Requirement (@talabahamkor)
        # Skip this check if it's a channel post, a broadcast forward, or the Owner
        is_media = isinstance(event, Message) and (event.document or event.photo or event.video)
        is_start = isinstance(event, Message) and event.text and event.text.startswith('/start')
        
        if (is_media or is_start) and not is_channel_post and not is_forwarded_channel:
            global_channel = "@talabahamkor"
            is_global_member = await self._is_member_of(data.get("bot"), user.id, global_channel)
            if not is_global_member:
                return await self._block_with_subscription(event, global_channel)

        # Check Cache
        now = datetime.utcnow()
        if user.id in self.cache:
            cache_entry = self.cache[user.id]
            if cache_entry["expiry"] > now and cache_entry["status"] is True:
                return await handler(event, data)
            
            # If we have the channel in cache, we can skip the DB query
            if "channel" in cache_entry and cache_entry["channel"]:
                channel_id_str = cache_entry["channel"]
                return await self._check_membership(handler, event, data, user, channel_id_str, now)

        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        # 2. Foydalanuvchi akkauntini topish (with optimized loading)
        from sqlalchemy.orm import selectinload
        account = await session.scalar(
            select(TgAccount)
            .where(TgAccount.telegram_id == user.id)
            .options(
                selectinload(TgAccount.staff).selectinload(Staff.university),
                selectinload(TgAccount.student).selectinload(Student.university),
            )
        )

        if not account:
            return await handler(event, data)

        university = None
        if account.staff and account.staff.university:
            university = account.staff.university
        elif account.student and account.student.university:
            university = account.student.university

        if not university or not university.required_channel:
            # Cache "no channel required" for 1 hour
            self.cache[user.id] = {"status": True, "expiry": now + timedelta(hours=1)}
            return await handler(event, data)

        channel_id_str = university.required_channel
        return await self._check_membership(handler, event, data, user, channel_id_str, now)

    async def _check_membership(self, handler, event, data, user, channel_id_str, now):
        # 5. A'zolikni tekshirish
        try:
            bot = data.get("bot")
            import asyncio
            try:
                member = await asyncio.wait_for(bot.get_chat_member(chat_id=channel_id_str, user_id=user.id), timeout=1.5)
                is_member = member.status in ("member", "administrator", "creator")
            except asyncio.TimeoutError:
                is_member = True # Fallback: allow through on timeout
            
            if is_member:
                # Cache status for 30 minutes, keeping channel info
                self.cache[user.id] = {
                    "status": True, 
                    "expiry": now + timedelta(minutes=30),
                    "channel": channel_id_str
                 }
                return await handler(event, data)
            
            # Not a member
            try:
                chat_info = await asyncio.wait_for(bot.get_chat(channel_id_str), timeout=1.5)
                invite_link = chat_info.invite_link or f"https://t.me/{chat_info.username}" if chat_info.username else "https://t.me/"
            except:
                invite_link = "https://t.me/"

            from keyboards.inline_kb import get_subscription_check_kb
            text = "🚫 <b>Diqqat!</b> Botdan foydalanish uchun quyidagi kanalga a'zo bo'lishingiz kerak."

            if isinstance(event, Message):
                await event.answer(text, reply_markup=get_subscription_check_kb(invite_link))
            elif isinstance(event, CallbackQuery):
                if event.data == "check_subscription":
                    await event.answer("❌ Hali ham a'zo emassiz!", show_alert=True)
                else:
                    try: await event.message.delete()
                    except: pass
                    await event.message.answer(text, reply_markup=get_subscription_check_kb(invite_link))
            return

        except Exception as e:
            logger.error(f"Subscription check CRITICAL failed for user {user.id}: {e}")
            return await handler(event, data)

    async def _is_member_of(self, bot, user_id: int, channel_id_str: str) -> bool:
        """Helper to quickly check membership with a short timeout."""
        if not bot:
            return True
        import asyncio
        try:
            member = await asyncio.wait_for(bot.get_chat_member(chat_id=channel_id_str, user_id=user_id), timeout=1.5)
            return member.status in ("member", "administrator", "creator")
        except asyncio.TimeoutError:
            return True # Fallback on timeout
        except Exception:
            return False

    async def _block_with_subscription(self, event, channel_id_str: str):
        """Blocks interaction and shows subscribe keyboard."""
        bot = event.bot
        import asyncio
        try:
            chat_info = await asyncio.wait_for(bot.get_chat(channel_id_str), timeout=1.5)
            invite_link = chat_info.invite_link or f"https://t.me/{chat_info.username}" if chat_info.username else "https://t.me/"
        except:
            invite_link = "https://t.me/"
            if channel_id_str.startswith("@"):
                invite_link += channel_id_str[1:]

        from keyboards.inline_kb import get_subscription_check_kb
        text = "🚫 <b>Diqqat!</b> Botga fayl yoki rasm yuklash uchun asosiy kanalimizga a'zo bo'lishingiz kerak."

        if isinstance(event, Message):
            await event.answer(text, reply_markup=get_subscription_check_kb(invite_link))
        elif isinstance(event, CallbackQuery):
            await event.answer("❌ Asosiy kanalga a'zo emassiz!", show_alert=True)
            try: await event.message.answer(text, reply_markup=get_subscription_check_kb(invite_link))
            except: pass
        return
