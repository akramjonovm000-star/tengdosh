import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        # Get sample image URLs
        stmt = select(Student.image_url).where(Student.image_url.is_not(None)).limit(20)
        result = await session.execute(stmt)
        urls = result.scalars().all()
        
        print("--- Sample Image URLs ---")
        for url in urls:
            print(url)
            
        # Check for potential 'default' text
        stmt_def = select(Student.image_url).where(Student.image_url.ilike("%default%")).limit(5)
        res_def = await session.execute(stmt_def)
        defaults = res_def.scalars().all()
        
        print("\n--- 'Default' string matches ---")
        for url in defaults:
            print(url)

if __name__ == "__main__":
    asyncio.run(main())
