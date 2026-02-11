import asyncio
from sqlalchemy import delete
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaComment

async def delete_comment(comment_id: int):
    async with AsyncSessionLocal() as session:
        print(f"Deleting comment ID: {comment_id}...")
        stmt = delete(ChoyxonaComment).where(ChoyxonaComment.id == comment_id)
        await session.execute(stmt)
        await session.commit()
        print("Success: Comment deleted.")

if __name__ == "__main__":
    # We saw ID 151 in the previous step
    asyncio.run(delete_comment(151))
