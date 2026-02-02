
import logging
import asyncio
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from bot import bot
from database.db_connect import AsyncSessionLocal
from database.models import Election, ElectionCandidate, ElectionVote, Student, TgAccount

logger = logging.getLogger(__name__)

class ElectionService:
    @staticmethod
    async def finish_election(election_id: int, session: AsyncSession):
        """
        Saylovni yakunlaydi va g'oliblarni e'lon qiladi.
        """
        election = await session.get(Election, election_id)
        if not election:
            logger.error(f"Election {election_id} not found")
            return

        if election.status == "finished":
             logger.warning(f"Election {election_id} already finished")
             return

        logger.info(f"Finishing election: {election.title} (ID: {election_id})")
        
        # 1. Statusni yangilash
        election.status = "finished"
        await session.commit()
        logger.info(f"Election {election_id} status set to finished. Broadcasting disabled.")
            
    @staticmethod
    async def send_announcement(chat_id: int, text: str, photo_id: str | None):
        try:
            if photo_id:
                await bot.send_photo(chat_id=chat_id, photo=photo_id, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        except Exception as e:
            # Bot blocked or other error
            logger.warning(f"Failed to send result to {chat_id}: {e}")

    @staticmethod
    async def check_deadlines():
        """
        Har 30 daqiqada ishga tushib, deadline o'tgan saylovlarni yopadi.
        """
        async with AsyncSessionLocal() as session:
            # Active va deadline o'tgan saylovlarni topish
            now = datetime.utcnow()
            stmt = select(Election).where(
                and_(
                    Election.status == "active",
                    Election.deadline != None,
                    Election.deadline < now
                )
            )
            expired_elections = (await session.scalars(stmt)).all()
            
            if not expired_elections:
                return

            logger.info(f"Found {len(expired_elections)} expired elections. Finishing them...")
            for election in expired_elections:
                await ElectionService.finish_election(election.id, session)
