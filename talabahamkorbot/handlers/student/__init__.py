from aiogram import Router

from .profile import router as profile_router
from .activities import router as activities_router
from .documents import router as documents_router
from .certificates import router as certificates_router
from .tyutor_contact import router as tyutor_contact_router
from .navigation import router as navigation_router
from .feedback import router as feedback_router
from .academic import router as academic_router
from .surveys import router as surveys_router

router = Router()

router.include_router(profile_router)
router.include_router(activities_router)
router.include_router(documents_router)
router.include_router(certificates_router)
router.include_router(tyutor_contact_router)
router.include_router(navigation_router)
router.include_router(feedback_router)
router.include_router(academic_router)
router.include_router(surveys_router)
