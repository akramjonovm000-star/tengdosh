
import asyncio
import logging
from typing import Dict
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Banner
from database.db_connect import AsyncSessionLocal

logger = logging.getLogger(__name__)

class BannerAnalyticsService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BannerAnalyticsService, cls).__new__(cls)
            cls._instance._views_buffer: Dict[int, int] = {}
            cls._instance._clicks_buffer: Dict[int, int] = {}
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def increment_view(self, banner_id: int):
        async with self._lock:
            self._views_buffer[banner_id] = self._views_buffer.get(banner_id, 0) + 1

    async def increment_click(self, banner_id: int):
        async with self._lock:
            self._clicks_buffer[banner_id] = self._clicks_buffer.get(banner_id, 0) + 1

    async def flush(self):
        """Writes buffered data to database"""
        async with self._lock:
            if not self._views_buffer and not self._clicks_buffer:
                return
            
            views_to_write = self._views_buffer.copy()
            clicks_to_write = self._clicks_buffer.copy()
            self._views_buffer.clear()
            self._clicks_buffer.clear()

        if not views_to_write and not clicks_to_write:
            return

        logger.info(f"Flushing banner analytics: {len(views_to_write)} views, {len(clicks_to_write)} clicks updates")
        
        async with AsyncSessionLocal() as session:
            try:
                # Update views
                for banner_id, count in views_to_write.items():
                    await session.execute(
                        update(Banner)
                        .where(Banner.id == banner_id)
                        .values(views=Banner.views + count)
                    )
                
                # Update clicks
                for banner_id, count in clicks_to_write.items():
                    await session.execute(
                        update(Banner)
                        .where(Banner.id == banner_id)
                        .values(clicks=Banner.clicks + count)
                    )
                
                await session.commit()
            except Exception as e:
                logger.error(f"Error flushing banner analytics: {e}")
                # We could try to restore buffer here, but for analytics, data loss is acceptable vs complex retry logic
