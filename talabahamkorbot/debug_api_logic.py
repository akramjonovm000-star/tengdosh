import asyncio
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment, Student

# Mocking the map function based on api/community.py logic
def _map_comment_mock(comment, author, current_user_id):
    reply_user = None
    reply_content = None
    
    if comment.parent_comment:
        reply_user = comment.parent_comment.student.full_name if comment.parent_comment.student else "Noma'lum"
        reply_content = comment.parent_comment.content

    is_liked = any(l.student_id == current_user_id for l in comment.likes) if comment.likes else False
    
    # Mocking logic for is_liked_by_author (simplified)
    is_liked_by_author = False
    if comment.post and comment.likes:
         is_liked_by_author = any(l.student_id == comment.post.student_id for l in comment.likes)

    return {
        "id": comment.id,
        "content": comment.content,
        "author_name": author.full_name if author else "Noma'lum",
        "created_at": str(comment.created_at),
        "is_mine": (comment.student_id == current_user_id)
    }

async def debug_api_logic():
    post_id = 36 # Determined from previous step
    current_user_id = 1 # Mock user

    async with AsyncSessionLocal() as db:
        print(f"🔍 Querying comments for Post {post_id}...")
        
        # Exact query from api/community.py
        query = select(ChoyxonaComment).options(
            selectinload(ChoyxonaComment.student),
            selectinload(ChoyxonaComment.parent_comment).selectinload(ChoyxonaComment.student),
            selectinload(ChoyxonaComment.likes),
            selectinload(ChoyxonaComment.post)
        ).where(ChoyxonaComment.post_id == post_id).order_by(ChoyxonaComment.created_at)
        
        try:
            result = await db.execute(query)
            comments = result.scalars().all()
            print(f"✅ Query Successful. Rows found: {len(comments)}")
            
            print("🔄 Attempting Mapping...")
            mapped = []
            for c in comments:
                m = _map_comment_mock(c, c.student, current_user_id)
                mapped.append(m)
            
            print(f"✅ Mapping Successful. Items: {len(mapped)}")
            if len(mapped) > 0:
                print(f"Example: {mapped[0]}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_logic())
