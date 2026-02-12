import asyncio
import sys
import os

# Add talabahamkorbot directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database.db_connect import AsyncSessionLocal
from database.models import Banner

async def create_banners():
    file_id = "AgACAgIAAxkBAAIu-GmHKazz36c25Tz03YpbLJODXJ4pAAK8D2sbEQ84SEswFoW28NngAQADAgADeQADOgQ"
    
    async with AsyncSessionLocal() as db:
        # Create Banner 1
        b1 = Banner(
            image_file_id=file_id,
            link="https://t.me/talabahamkor_bot",
            is_active=True
        )
        db.add(b1)
        
        # Create Banner 2
        b2 = Banner(
            image_file_id=file_id,
            link="https://jmcu.uz",
            is_active=True
        )
        db.add(b2)
        
        await db.commit()
        print("Created 2 demo banners!")

if __name__ == "__main__":
    asyncio.run(create_banners())
