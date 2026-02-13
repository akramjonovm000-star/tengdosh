
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, StaffRole, TgAccount
from handlers.auth import get_current_user

# Copy is_admin from clubs.py
async def is_admin(user) -> bool:
    if not hasattr(user, "role"):
        print("DEBUG: User has no role attribute")
        return False
        
    allowed_roles = [
        StaffRole.OWNER.value, 
        StaffRole.DEVELOPER.value,
        StaffRole.RAHBARIYAT.value,
        StaffRole.DEKANAT.value,
        StaffRole.YOSHLAR_PROREKTOR.value,
        StaffRole.YOSHLAR_YETAKCHISI.value
    ]
    
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    print(f"DEBUG: role_value='{role_value}'")
    print(f"DEBUG: allowed_roles={allowed_roles}")
    
    result = role_value in allowed_roles
    print(f"DEBUG: result={result}")
    return result

async def check():
    async with AsyncSessionLocal() as session:
        tid = 7476703866
        user = await get_current_user(tid, session)
        if not user:
            print("DEBUG: User not found")
            return
            
        print(f"DEBUG: User object type={type(user)}")
        await is_admin(user)

if __name__ == "__main__":
    asyncio.run(check())
