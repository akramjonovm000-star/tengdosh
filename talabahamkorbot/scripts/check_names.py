import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_names():
    async with AsyncSessionLocal() as db:
        # Check Javohirxon Token
        res = await db.execute(select(Student.hemis_token).where(Student.hemis_login == '395251101397'))
        token = res.scalar()
        
        if token:
            from services.hemis_service import HemisService
            me = await HemisService.get_me(token)
            print(f"HEMIS ME: {me}")
        else:
            print("No token found for Javohirxon")

if __name__ == "__main__":
    asyncio.run(check_names())
