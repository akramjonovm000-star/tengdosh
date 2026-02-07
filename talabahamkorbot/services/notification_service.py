import logging
import os
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional, List
import asyncio
from celery_app import app as celery_app
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

logger = logging.getLogger(__name__)

class NotificationService:
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if cls._initialized:
            return

        # Look for credentials file
        key_path = os.environ.get("FIREBASE_KEY_PATH", "firebase-key.json")
        
        if os.path.exists(key_path):
            try:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                logger.info("🚀 Firebase Admin initialized successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Firebase Admin: {e}")
        else:
            logger.warning(f"⚠️ Firebase credentials not found at {key_path}. Push notifications will be disabled.")

    @classmethod
    async def send_push(cls, token: str, title: str, body: str, data: Optional[dict] = None):
        """Send a push notification to a specific FCM token (Async Wrapper)"""
        return await asyncio.to_thread(cls._send_push_sync, token, title, body, data)

    @classmethod
    def _send_push_sync(cls, token: str, title: str, body: str, data: Optional[dict] = None):
        if not cls._initialized:
            cls.initialize()
            if not cls._initialized:
                return False

        if not token:
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )
            response = messaging.send(message)
            logger.info(f"✅ Push sent successfully: {response}")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending push notification: {e}")
            return False

    @classmethod
    async def send_multicast(cls, tokens: List[str], title: str, body: str, data: Optional[dict] = None):
        """Send push notifications to multiple FCM tokens (Async Wrapper)"""
        return await asyncio.to_thread(cls._send_multicast_sync, tokens, title, body, data)

    @classmethod
    def _send_multicast_sync(cls, tokens: List[str], title: str, body: str, data: Optional[dict] = None):
        if not cls._initialized:
            cls.initialize()
            if not cls._initialized:
                return False

        if not tokens:
            return False

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )
            response = messaging.send_multicast(message)
            logger.info(f"✅ Multicast push sent. Success: {response.success_count}, Failure: {response.failure_count}")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending multicast push: {e}")
            return False

    @classmethod
    @celery_app.task(name="broadcast_push")
    def run_broadcast(cls, title: str, body: str, data: Optional[dict] = None):
        """Celery entry point for broadcast"""
        # Since this is a classmethod being used as a task, we need to handle it carefully
        # Celery might not pass 'cls'. But calling it via @app.task might work if defined outside.
        # Actually, for Celery, it's safer to have a flat function or use 'bind'
        return asyncio.run(NotificationService.broadcast_push(title, body, data))

    @classmethod
    async def broadcast_push(cls, title: str, body: str, data: Optional[dict] = None):
        """Fetch all tokens and send in chunks"""
        logger.info(f"📣 Starting broadcast: {title}")
        
        async with AsyncSessionLocal() as session:
            # Fetch all students with a token
            stmt = select(Student.fcm_token).where(Student.fcm_token.is_not(None))
            result = await session.execute(stmt)
            tokens = [t for t in result.scalars().all() if t]

        if not tokens:
            logger.info("ℹ️ No FCM tokens found to broadcast.")
            return

        # Firebase Multicast limit 500 tokens per call
        chunk_size = 500
        for i in range(0, len(tokens), chunk_size):
            chunk = tokens[i : i + chunk_size]
            await cls.send_multicast(chunk, title, body, data)
        
        logger.info(f"✅ Broadcast finished. Total tokens: {len(tokens)}")

