import asyncio
from sqlalchemy import select, desc, or_
from database.db_connect import AsyncSessionLocal
from database.models import PrivateChat, PrivateMessage, Student

async def check():
    async with AsyncSessionLocal() as db:
        print("--- Checking ALL Chats for User 730 ---")
        chats = await db.scalars(
            select(PrivateChat).where(
                or_(PrivateChat.user1_id == 730, PrivateChat.user2_id == 730)
            )
        )
        
        for chat in chats:
            print(f"Chat ID: {chat.id}")
            print(f"  User1: {chat.user1_id} (Unread: {chat.user1_unread_count})")
            print(f"  User2: {chat.user2_id} (Unread: {chat.user2_unread_count})")
            print(f"  Last Message: {chat.last_message_content}")
            print(f"  Last Time: {chat.last_message_time}")
            
asyncio.run(check())
