from django.urls import path
from api.v1.views.user import LoginView, MeView, StudentsView, StudentFilterParamsView, StudentExportExcelView
from api.v1.views.application import ApplicationExportExcelView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('students/', StudentsView.as_view(), name='students'),
    path('students/filter/', StudentFilterParamsView.as_view(), name='faculties'),
    path('students/excel/', ApplicationExportExcelView.as_view(), name='students_excel')
]
