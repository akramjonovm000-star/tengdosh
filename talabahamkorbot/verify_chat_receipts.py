import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import PrivateMessage, PrivateChat

async def verify_read_receipts():
    async with AsyncSessionLocal() as db:
        # 1. Find a chat with unread messages
        stmt = select(PrivateMessage).where(PrivateMessage.is_read == False).limit(5)
        res = await db.execute(stmt)
        msgs = res.scalars().all()
        
        if not msgs:
            print("No unread messages found to test with.")
            # Create a dummy if needed, but let's check existing first
            return

        print(f"Found {len(msgs)} unread messages.")
        for m in msgs:
            print(f" Msg ID: {m.id}, Chat ID: {m.chat_id}, Sender: {m.sender_id}, Content: {m.content[:20]}")

        # Simulate marking as read from perspective of recipient
        # Pick one chat
        test_chat_id = msgs[0].chat_id
        test_student_id = 0 # Dummy, for testing we just want to see if marking works
        # If msg sender is X, student is Y
        sender_id = msgs[0].sender_id
        recipient_id = 999999 # Dummy recipient
        
        print(f"\nSimulating marking messages in chat {test_chat_id} as read (from recipient != {sender_id})...")
        
        from sqlalchemy import update, and_
        update_stmt = update(PrivateMessage).where(
            and_(
                PrivateMessage.chat_id == test_chat_id,
                PrivateMessage.sender_id != recipient_id, # In real logic it is != student.id
                PrivateMessage.is_read == False
            )
        ).values(is_read=True)
        await db.execute(update_stmt)
        await db.commit()
        
        # Verify
        res = await db.execute(select(PrivateMessage).where(PrivateMessage.id == msgs[0].id))
        updated_msg = res.scalar_one()
        print(f"Verification: Msg ID {updated_msg.id} is_read = {updated_msg.is_read}")

if __name__ == "__main__":
    asyncio.run(verify_read_receipts())
