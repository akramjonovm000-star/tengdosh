from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def api_root():
    return {"status": "active", "version": "v1"}

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
from .tutor import router as tutor_router
from .ai import router as ai_router
from .community import router as community_router
from .market import router as market_router
from .notifications import router as notifications_router
from .payment import router as payment_router
from .subscription import router as subscription_router
from .chat import router as chat_router
from .gpa import router as gpa_router
from .plans import router as plans_router
from .management import router as management_router
from .management_appeals import router as management_appeals_router
from .management_appeals import router as management_appeals_router
from .banner import router as banner_router
from .announcements import router as announcements_router


# 1. CORE & AUTH
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(oauth_router, tags=["OAuth"])
router.include_router(files_router, prefix="/files", tags=["Files"])

# 2. STUDENT ACADEMIC (Mounted under /student for App compatibility)
# Route conflict fix: Specific academic routes MUST come before generic /{student_id}
router.include_router(academic_router, prefix="/student", tags=["Academic (Student)"])
router.include_router(academic_router, prefix="/education", tags=["Academic"])

# 3. STUDENT FEATURES
router.include_router(dashboard_router, prefix="/student/dashboard", tags=["Dashboard"])
router.include_router(activities_router, prefix="/student/activities", tags=["Activities"])
router.include_router(clubs_router, prefix="/student/clubs", tags=["Clubs"])
router.include_router(feedback_router, prefix="/student/feedback", tags=["Feedback"])
router.include_router(surveys_router, prefix="/student", tags=["Surveys"])
router.include_router(notifications_router, prefix="/student/notifications", tags=["Notifications"])
router.include_router(documents_router, prefix="/student/documents", tags=["Documents"])
router.include_router(certificates_router, prefix="/student/certificates", tags=["Certificates"])
# Support for legacy /api/v1/documents/send path
router.include_router(documents_router, prefix="/documents", tags=["Documents (Legacy)"])

# 4. SOCIAL & COMMUNITY
router.include_router(community_router, prefix="/community", tags=["Community"])
router.include_router(subscription_router, prefix="/community", tags=["Subscription"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(banner_router, tags=["Banner"])
router.include_router(announcements_router, tags=["Announcements"])


# 5. OTHER SERVICES
router.include_router(ai_router, prefix="/ai", tags=["AI"])
router.include_router(market_router, prefix="/market", tags=["Market"])
router.include_router(payment_router, prefix="/payment", tags=["Payment"])
router.include_router(gpa_router, prefix="/gpa", tags=["GPA"])
router.include_router(plans_router, prefix="/plans", tags=["Plans"])
router.include_router(election_router, prefix="/election", tags=["Election"])
router.include_router(management_router, tags=["Management"])
router.include_router(management_appeals_router, tags=["Management Appeals"])
router.include_router(tutor_router, tags=["Tutor"])



# 6. GENERIC STUDENT PROFILE (Wildcard /{student_id} at the end)
# This MUST be last to avoid catching specific /student/... routes
router.include_router(student_router, prefix="/student", tags=["Student"])

