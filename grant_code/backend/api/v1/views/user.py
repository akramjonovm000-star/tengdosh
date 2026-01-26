from rest_framework import permissions, generics, status, views
from rest_framework.response import Response
from rest_framework import filters
from django.utils import timezone
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.jwt_auth import set_jwt_cookies
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.jwt_auth import JWTAuthentication, JWTCookieAuthentication
from api.v1.serializers.user import LoginSerializer, UserSerializer, StudentSerializer
from api.v1.filters.user import StudentFilter
from apps.user.models import Student
from core.pagination import PageNumberPagination
from api.v1.permissions.application import IsInspector

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import pandas as pd
from io import BytesIO


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')
    serializer_class = LoginSerializer

    user = None
    access_token = None
    token = None

    def get_response(self):
        serializer_class = api_settings.JWT_SERIALIZER

        data = {
            'user': self.user,
            'access': self.access_token,
            'refresh': self.refresh_token,
        }

        serializer = serializer_class(
            instance=data,
            context=self.get_serializer_context(),
        )

        response = Response(serializer.data, status=status.HTTP_200_OK)
        set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response

    def post(self, request, *args, **kwargs):
        self.request = request
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        self.user = serializer.validated_data['user']

        self.access_token, self.refresh_token = jwt_encode(self.user)
        return self.get_response()


class MeView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class StudentsView(generics.ListAPIView):
    queryset = Student.objects.filter(applications__isnull=False, applications__is_rejected=False).distinct().order_by('-score')
    # queryset = Student.objects.all().order_by('-score')
    pagination_class = PageNumberPagination
    serializer_class = StudentSerializer
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = StudentFilter
    ordering_fields = ['score']
    # authentication_classes = [JWTAuthentication, JWTCookieAuthentication]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id', openapi.IN_QUERY, description="ID (exact match)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('full_name', openapi.IN_QUERY,
                              description="Full name contains", type=openapi.TYPE_STRING),
            openapi.Parameter('speciality', openapi.IN_QUERY,
                              description="Speciality contains", type=openapi.TYPE_STRING),
            openapi.Parameter('education_form', openapi.IN_QUERY,
                              description="Education form contains", type=openapi.TYPE_STRING),
            openapi.Parameter('level', openapi.IN_QUERY,
                              description="Level exact match", type=openapi.TYPE_INTEGER),
            openapi.Parameter('group', openapi.IN_QUERY,
                              description="Group contains", type=openapi.TYPE_STRING),
            openapi.Parameter('faculty', openapi.IN_QUERY,
                              description="Faculty contains", type=openapi.TYPE_STRING),
            openapi.Parameter('education_type', openapi.IN_QUERY,
                              description="Education type contains", type=openapi.TYPE_STRING),
            openapi.Parameter('payment_type', openapi.IN_QUERY,
                              description="Payment type contains", type=openapi.TYPE_STRING),
            openapi.Parameter('gpa', openapi.IN_QUERY, description="GPA exact match",
                              type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class StudentExportExcelView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsInspector)
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    queryset = Student.objects.filter(applications__isnull=False).order_by('faculty', 'speciality', 'group', "level", "score")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().values("user__username", "full_name", "level", "faculty", "speciality", "group", "education_type", "education_language", "education_score", "social_score").distinct()

        df = pd.DataFrame(list(queryset))
        df.rename(columns={
            'user__username': 'ID',
            'full_name': 'FIO',
            'level': 'Kurs',
            'faculty': 'Fakultet',
            'speciality': 'Yo\'nalish',
            'group': 'Guruh',
            'education_type': 'Ta\'lim Turi',
            'education_language': 'Ta\'lim Tili',
            'education_score': 'Ta\'lim Balli',
            'social_score': 'Ijtimoiy Balli'
        }, inplace=True)
        buffer = BytesIO()
       
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
            worksheet = writer.sheets['Students']
            for idx, col in enumerate(df):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(idx, idx, max_length)
            
            header_format = writer.book.add_format({'bold': True, 'font_color': 'black', 'bg_color': '#D9EAD3'})
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="students.xlsx"'
        return response


class StudentFilterParamsView(views.APIView):
    def get(self, request, *args, **kwargs):
        edu_lang = request.query_params.get('edu_lang', "")
        edu_type = request.query_params.get('edu_type', "")
        faculty = request.query_params.get('faculty', "")

        faculties = Student.objects.filter(education_language__icontains=edu_lang, education_type__icontains=edu_type).values_list(
            'faculty', flat=True).distinct().order_by('faculty')
        specialities = Student.objects.filter(faculty__icontains=faculty, education_language__icontains=edu_lang, education_type__icontains=edu_type).values_list(
            'speciality', flat=True).distinct().order_by('speciality')
        education_types = Student.objects.values_list(
            'education_type', flat=True).distinct().order_by('education_type')

        return Response({
            'faculties': faculties,
            'specialities': specialities,
            'education_types': education_types
        }, status=status.HTTP_200_OK)
