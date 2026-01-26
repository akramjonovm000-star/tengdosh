from django.urls import path
from api.v1.views.application import (
    AppealViewSet,
    ApplicationViewSet,
    AttemptViewSet,
    ApplicationFileUploadView,
    ApplicationCriterionScoreView,
    QuotaView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"appeal", AppealViewSet, basename="appeal")
router.register(r"applications", ApplicationViewSet, basename="application")
router.register(r"applications/test/attempts", AttemptViewSet, basename="attempt")

urlpatterns = router.urls + [
    path("quotas/", QuotaView.as_view(), name="quota-list"),
    path("applications/<int:application_id>/criterion/<int:criterion_id>/upload/",
         ApplicationFileUploadView.as_view(), name="file-upload"),
    path("applications/<int:application_id>/criterion/<int:criterion_id>/score/",
         ApplicationCriterionScoreView.as_view(), name="criterion-score-upload"),
]
