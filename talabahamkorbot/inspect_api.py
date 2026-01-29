
import asyncio
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import Student, ChoyxonaPost
from api.community import _map_post
import json

async def inspect_raw_posts():
    async with AsyncSessionLocal() as session:
        # Simulate /posts logic
        query = select(ChoyxonaPost).options(
            selectinload(ChoyxonaPost.student), 
            selectinload(ChoyxonaPost.likes), 
            selectinload(ChoyxonaPost.reposts)
        ).where(ChoyxonaPost.category_type == 'specialty').order_by(desc(ChoyxonaPost.created_at)).limit(5)
        
        result = await session.execute(query)
        posts = result.scalars().all()
        
        # We need a dummy current_user_id
        dummy_id = 0
        
        raw_data = []
        for p in posts:
            mapped = _map_post(p, p.student, dummy_id)
            # Convert Pydantic to Dict
            data = json.loads(mapped.model_dump_json())
            raw_data.append({
                "author": data['author_name'],
                "is_premium": data['author_is_premium'],
                "content_preview": data['content'][:20]
            })
            
        print(json.dumps(raw_data, indent=2))

if __name__ == "__main__":
    asyncio.run(inspect_raw_posts())
