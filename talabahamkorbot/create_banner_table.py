
import asyncio
from database.db_connect import engine
from database.models import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

class Banner(Base):
    __tablename__ = "banners"
    
    id = Column(Integer, primary_key=True)
    image_file_id = Column(String(255), nullable=False) # Telegram File ID
    link = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

async def create_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Banner table created (if not exists).")

if __name__ == "__main__":
    asyncio.run(create_table())
