import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select
from api.security import create_access_token
from utils.encryption import encrypt_data

async def get_token_for_sanjar():
    async with AsyncSessionLocal() as db:
        stmt = select(Staff).where(Staff.id == 84) # Sanjar Botirovich
        sanjar = (await db.execute(stmt)).scalars().first()
        if not sanjar:
            print("Sanjar not found!")
            return
            
        encrypted_token = encrypt_data("some_hemis_token")
        
        access_token = create_access_token(
            data={
                "sub": sanjar.full_name,
                "type": "staff",
                "id": sanjar.id,
                "hemis_token": encrypted_token,
                "ua": "test_hash"
            }
        )
        print(access_token)

if __name__ == '__main__':
    asyncio.run(get_token_for_sanjar())
