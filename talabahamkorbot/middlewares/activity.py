
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount

logger = logging.getLogger(__name__)

class ActivityMiddleware(BaseMiddleware):
    """
    Tracks user activity by updating 'last_active' field in TgAccount.
    Uses in-memory cache to throttle DB updates (e.g., update once per hour).
    """

    def __init__(self):
        super().__init__()
        # Cache format: {user_id: last_update_datetime}
        self.cache: Dict[int, datetime] = {}
        self.THROTTLE_TIMEDELTA = timedelta(hours=1)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        if not user or user.is_bot:
            return await handler(event, data)

        # Check throttling
        now = datetime.utcnow()
        last_update = self.cache.get(user.id)
        
        if last_update and (now - last_update) < self.THROTTLE_TIMEDELTA:
            # Skip DB update, just proceed
            return await handler(event, data)

        # Update DB
        session: AsyncSession = data.get("session")
        if session:
            try:
                # Optimized update without fetch
                await session.execute(
                    update(TgAccount)
                    .where(TgAccount.telegram_id == user.id)
                    .values(last_active=now)
                )
                # await session.commit()
                # Defer commit to handler or session close to reduce latency per message
                
                # Update cache
                self.cache[user.id] = now
                # logger.debug(f"Activity updated for user {user.id}")
                
            except Exception as e:
                logger.warning(f"Failed to update activity for {user.id}: {e}")

        return await handler(event, data)
