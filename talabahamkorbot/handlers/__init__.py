from aiogram import Router
from .subscription import router as subscription_router

# ===================== AUTH =====================
from .deep_link_auth import router as deep_link_auth_router

# ===================== OWNER =====================
from .owner import router as owner_router
from .owner_gifts import router as owner_gifts_router
from .admin import admin_router
from .admin.clubs import router as admin_clubs_router 

from .student.documents import router as student_documents_router

# Create root router at module level
root_router = Router()

# 1. AUTH & SYSTEM
root_router.include_router(subscription_router)
root_router.include_router(deep_link_auth_router)

# 2. STUDENT
from .clubs_sync import router as clubs_sync_router
from .student.club_event import router as club_event_router
from .student.housing import router as housing_router
from .student.dorm import router as dorm_router
root_router.include_router(student_documents_router)
root_router.include_router(clubs_sync_router)
root_router.include_router(club_event_router)
root_router.include_router(housing_router)
root_router.include_router(dorm_router)

# 3. OWNER
root_router.include_router(owner_router)
root_router.include_router(owner_gifts_router)
root_router.include_router(admin_router)
root_router.include_router(admin_clubs_router) 

def setup_routers() -> Router:
    return root_router
