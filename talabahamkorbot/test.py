import asyncio
from httpx import AsyncClient

async def main():
    # Login as Javohirxon
    from database.db_connect import AsyncSessionLocal
    from database.models import Student
    from sqlalchemy import select
    from services.token_service import TokenService
    
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(Student).where(Student.username == 'javohirxon'))
        user_id = user.id
        # get reposts via API directly
        from api.community import get_reposted_posts
        try:
             res = await get_reposted_posts(target_student_id=user_id, student=user, db=db)
             print(f"Direct API call returned {len(res)} items")
        except Exception as e:
             import traceback
             traceback.print_exc()

asyncio.run(main())
