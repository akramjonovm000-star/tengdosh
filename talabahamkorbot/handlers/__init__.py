from aiogram import Router
from .subscription import router as subscription_router

# ===================== AUTH =====================
from .auth import router as auth_router
from .registration import router as registration_router
from .demo import router as demo_router
from .clubs import router as clubs_router
from .ai_chat import router as ai_chat_router

# ===================== OWNER =====================
from .owner import router as owner_router
from .owner_gifts import router as owner_gifts_router
from .admin import admin_router
from .admin.clubs import router as admin_clubs_router # [NEW]

# ===================== STUDENT =====================
# ===================== STUDENT =====================
from .student import router as student_router

# ===================== STAFF =====================
from .staff.auth import router as staff_auth_router
from .staff.rahbariyat import router as staff_rahbariyat_router
from .staff.dekanat import router as staff_dekanat_router
from .staff.tutor import router as staff_tutor_router
from .staff.activity_approval import router as staff_activity_approval_router
# from .staff.feedback import router as staff_feedback_router
from .staff.appeals import router as staff_appeals_router
from .staff.broadcast import router as staff_broadcast_router
from .staff.student_lookup import router as staff_student_lookup_router
from .staff.dashboard import router as staff_dashboard_router
from .staff.dashboard import router as staff_dashboard_router
from .staff.tyutor_monitoring import router as staff_tyutor_monitoring_router
from .staff.tyutor_approval import router as staff_tyutor_approval_router # <--- NEW
from .staff.mobile_broadcast import router as mobile_broadcast_router

# ===================== TYUTOR (NEW MODULE) =====================
from .tyutor import router as tyutor_router


# Create root router at module level
root_router = Router()

# 1. AUTH & SYSTEM
root_router.include_router(subscription_router)
root_router.include_router(auth_router)
root_router.include_router(registration_router)
root_router.include_router(demo_router)
root_router.include_router(clubs_router)
root_router.include_router(ai_chat_router)
from .deep_link_auth import router as deep_link_auth_router
root_router.include_router(deep_link_auth_router)

# 2. OWNER
root_router.include_router(owner_router)
root_router.include_router(owner_gifts_router)
root_router.include_router(admin_router)
root_router.include_router(admin_clubs_router) # [NEW]

# 3. TYUTOR (PRIORITY OVER STAFF)
# Bu juda muhim, chunki Staff routerlari "tyutor" callbacklarini ushlab qolishi mumkin.
root_router.include_router(tyutor_router)

# 4. STAFF
root_router.include_router(staff_tyutor_monitoring_router)
root_router.include_router(staff_tyutor_approval_router) # <--- NEW
root_router.include_router(staff_student_lookup_router)
root_router.include_router(staff_dashboard_router)
root_router.include_router(staff_auth_router)
root_router.include_router(staff_rahbariyat_router)
root_router.include_router(staff_dekanat_router)
root_router.include_router(staff_tutor_router)
root_router.include_router(staff_activity_approval_router)
root_router.include_router(staff_appeals_router)
root_router.include_router(staff_broadcast_router)
root_router.include_router(mobile_broadcast_router)

# 5. STUDENT
root_router.include_router(student_router)


def setup_routers() -> Router:
    return root_router
