from fastapi import APIRouter

router = APIRouter()

from .auth import router as auth_router
from .student import router as student_router
from .activities import router as activities_router
from .dashboard import router as dashboard_router
from .clubs import router as clubs_router
from .feedback import router as feedback_router
from .documents import router as documents_router
from .certificates import router as certificates_router
from .academic import router as academic_router
from .oauth import router as oauth_router
from .files import router as files_router
from .surveys import router as surveys_router
from .election import router as election_router

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(oauth_router, tags=["OAuth"])
router.include_router(dashboard_router, prefix="/student/dashboard", tags=["Dashboard"])
router.include_router(activities_router, prefix="/student/activities", tags=["Activities"])
router.include_router(clubs_router, prefix="/student/clubs", tags=["Clubs"])
router.include_router(feedback_router, prefix="/student/feedback", tags=["Feedback"])


# Certificates and Documents routers ALREADY have prefixes in their files
router.include_router(documents_router, tags=["Documents"])
router.include_router(certificates_router, tags=["Certificates"])

router.include_router(academic_router, prefix="/education", tags=["Education"])
router.include_router(files_router, prefix="/files", tags=["Files"])

from .ai import router as ai_router
router.include_router(ai_router)

from .community import router as community_router
router.include_router(community_router, prefix="/community", tags=["Community"])

from .market import router as market_router
router.include_router(market_router)

from .notifications import router as notifications_router
router.include_router(notifications_router, prefix="/student/notifications", tags=["Notifications"])

from .payment import router as payment_router
router.include_router(payment_router)

from .subscription import router as subscription_router
router.include_router(subscription_router, prefix="/community", tags=["Subscription"])

from .chat import router as chat_router
router.include_router(chat_router, prefix="/chat", tags=["Chat"])

from .gpa import router as gpa_router
router.include_router(gpa_router, prefix="/gpa", tags=["GPA"])

from .plans import router as plans_router
router.include_router(plans_router, prefix="/plans", tags=["Plans"])
router.include_router(student_router, prefix="/student", tags=["Student"])
router.include_router(election_router, prefix="/election", tags=["Election"])
