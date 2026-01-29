from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_connect import get_session_factory


class DbSessionMiddleware(BaseMiddleware):
    """Har bir update uchun alohida AsyncSession ochib-yopib beradi."""

    def __init__(self):
        super().__init__()
        self.session_factory = get_session_factory()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session  # handlers ichida 'session: AsyncSession' sifatida olasiz
            return await handler(event, data)
