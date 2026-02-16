import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import SecurityToken, Student, Staff
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class TokenService:
import hashlib

    @staticmethod
    def _hash_token(token: str) -> str:
        """Returns SHA256 hash of the token."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    async def generate_batch(db: AsyncSession, user_id: int, user_type: str = "student", count: int = 500):
        """
        Generates a batch of unique tokens for the user.
        Uses bulk insert for performance.
        STORES HASHED TOKENS IN DB. RETURNS RAW TOKENS TO USER.
        """
        tokens_db = []
        tokens_raw = []
        now = datetime.utcnow()
        
        # Determine user ID field
        student_id = user_id if user_type == "student" else None
        staff_id = user_id if user_type == "staff" else None
        
        for _ in range(count):
            token_raw = uuid.uuid4().hex
            token_hash = TokenService._hash_token(token_raw)
            
            tokens_raw.append(token_raw)
            tokens_db.append({
                "token": token_hash, # STORE HASH
                "student_id": student_id,
                "staff_id": staff_id,
                "status": "active",
                "issued_at": now
            })
            
        if tokens_db:
            await db.execute(insert(SecurityToken), tokens_db)
            await db.commit()
            
        return tokens_raw # Client gets raw keys

    @staticmethod
    async def consume_token(db: AsyncSession, token: str, user_id: int, action_meta: str = None) -> bool:
        """
        Consumes a token.
        Token input is RAW. We hash it to find in DB.
        """
        token_hash = TokenService._hash_token(token)
        
        stmt = select(SecurityToken).where(SecurityToken.token == token_hash)
        result = await db.execute(stmt)
        security_token = result.scalar_one_or_none()
        
        if not security_token:
            return False
            
        # Check ownership
        # Staff vs Student logic
        is_owner = False
        if security_token.student_id and security_token.student_id == user_id:
            is_owner = True
        elif security_token.staff_id and security_token.staff_id == user_id:
            is_owner = True
            
        if not is_owner:
            logger.warning(f"Security Alert: User {user_id} tried to use token belonging to another user.")
            return False
            
        if security_token.status != "active":
            logger.warning(f"Security Alert: Replay attack attempt with token")
            return False
            
        # Mark as used
        security_token.status = "used"
        security_token.used_at = datetime.utcnow()
        if action_meta:
            security_token.action_meta = action_meta
            
        await db.commit()
        return True

    @staticmethod
    async def cleanup_old_tokens(db: AsyncSession, days: int = 30):
        """Removes used tokens older than N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        # TODO: Implement cleanup logic if needed
        pass
