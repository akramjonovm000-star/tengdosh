import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select
from api.security import create_access_token
from utils.encryption import encrypt_data

async def get_token_for_user(staff_id):
    async with AsyncSessionLocal() as db:
        stmt = select(Staff).where(Staff.id == staff_id)
        staff = (await db.execute(stmt)).scalars().first()
        if not staff:
            print("Staff not found!")
            return
            
        encrypted_token = encrypt_data("test")
        
        access_token = create_access_token(
            data={
                "sub": staff.full_name,
                "type": "staff",
                "id": staff.id,
                "hemis_token": encrypted_token,
                "ua": "test_hash"
            }
        )
        print(f"Token for {staff.full_name} ({staff.role}):")
        print(access_token)

if __name__ == '__main__':
    asyncio.run(get_token_for_user(85)) # Dekan
