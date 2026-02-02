import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment, Student

async def visualize_comments(post_id: int):
    async with AsyncSessionLocal() as db:
        try:
            query = select(ChoyxonaComment).options(
                selectinload(ChoyxonaComment.student)
            ).where(ChoyxonaComment.post_id == post_id)
            
            result = await db.execute(query)
            all_comments = result.scalars().all()
            
            # Sort by Likes (Desc) then Created Date (Asc) as per API logic
            all_comments.sort(key=lambda x: (-(x.likes_count or 0), x.created_at))
            
            # Build tree
            children = {}
            roots = []
            comment_map = {c.id: c for c in all_comments}
            
            for c in all_comments:
                if not c.reply_to_comment_id or c.reply_to_comment_id not in comment_map:
                    roots.append(c)
                else:
                    parent_id = c.reply_to_comment_id
                    if parent_id not in children:
                        children[parent_id] = []
                    children[parent_id].append(c)

            print(f"\n💬 Comment Section for Post #{post_id} ({len(all_comments)} comments)\n" + "="*50)
            
            def render_node(comment, indent="", is_last=True):
                mark = "└── " if is_last else "├── "
                author = comment.student.full_name if comment.student else "Noma'lum"
                likes = f"❤️ {comment.likes_count}" if (comment.likes_count or 0) > 0 else ""
                
                content_preview = (comment.content[:40] + "...") if len(comment.content) > 40 else comment.content
                print(f"{indent}{mark}{author}: {content_preview} {likes}")
                
                child_list = children.get(comment.id, [])
                new_indent = indent + ("    " if is_last else "│   ")
                
                for i, child in enumerate(child_list):
                    render_node(child, new_indent, i == len(child_list) - 1)

            for i, root in enumerate(roots):
                render_node(root, "", i == len(roots) - 1)
            
            print("="*50 + "\n")
            
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(visualize_comments(40))
