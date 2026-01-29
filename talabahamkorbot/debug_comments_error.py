import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment, Student

# Copied from api/community.py to replicate issue
def _map_comment(comment, author, current_user_id):
    reply_user = None
    reply_content = None
    
    if comment.parent_comment:
        reply_user = comment.parent_comment.student.full_name if comment.parent_comment.student else "Noma'lum"
        reply_content = comment.parent_comment.content

    # Logic from api/community.py
    is_liked = any(l.student_id == current_user_id for l in comment.likes) if comment.likes else False
    
    is_liked_by_author = False
    # ERROR SOURCE CANDIDATE: comment.post might be None if not loaded?
    # But we use selectinload(ChoyxonaComment.post)
    if comment.post and comment.likes:
         is_liked_by_author = any(l.student_id == comment.post.student_id for l in comment.likes)

    return {
        "id": comment.id,
        "content": comment.content
    }

async def debug_error():
    post_id = 36 # The problematic post
    current_user_id = 1
    
    async with AsyncSessionLocal() as db:
        print(f"Testing GET /posts/{post_id}/comments ...")
        
        try:
            query = select(ChoyxonaComment).options(
                selectinload(ChoyxonaComment.student),
                selectinload(ChoyxonaComment.parent_comment).selectinload(ChoyxonaComment.student),
                selectinload(ChoyxonaComment.post), # Crucial for is_liked_by_author
                selectinload(ChoyxonaComment.likes)
            ).where(ChoyxonaComment.post_id == post_id).order_by(ChoyxonaComment.created_at)
            
            result = await db.execute(query)
            comments = result.scalars().all()
            
            print(f"✅ Found {len(comments)} comments.")
            
            for c in comments:
                # Simulate mapping
                try:
                    _map_comment(c, c.student, current_user_id)
                except Exception as e:
                    print(f"❌ Error Mapping Comment {c.id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            print("✅ All comments mapped successfully.")
            
        except Exception as e:
            print(f"❌ Database Query Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_error())
