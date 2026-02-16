from aiogram import Router
from .subscription import router as subscription_router

# ===================== AUTH =====================
from .deep_link_auth import router as deep_link_auth_router

# ===================== OWNER =====================
from .owner import router as owner_router
from .owner_gifts import router as owner_gifts_router
from .admin import admin_router
from .admin.clubs import router as admin_clubs_router 

# Create root router at module level
root_router = Router()

# 1. AUTH & SYSTEM
root_router.include_router(subscription_router)
root_router.include_router(deep_link_auth_router)

# 2. OWNER
root_router.include_router(owner_router)
root_router.include_router(owner_gifts_router)
root_router.include_router(admin_router)
root_router.include_router(admin_clubs_router) 

def setup_routers() -> Router:
    return root_router
