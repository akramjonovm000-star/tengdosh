from datetime import timedelta
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, F, Value, Case, When
from django.db.models.functions import Coalesce, TruncDate
from rest_framework import viewsets, mixins, serializers, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from dj_rest_auth.jwt_auth import JWTAuthentication, JWTCookieAuthentication
from api.v1.serializers.application import (
    ApplicationCreateSerializer,
    ApplicationSerializer,
    ApplicationFileUploadSerializer,
    ApplicationCriterionScoreSerializer,
    AnswerAttemptSerializer,
    AttemptCreateSerializer,
    AttemptSerializer,
    AppealSerializer,
    AppealCreateSerializer,
    AppealApproveSerializer,
    QuotaSerializer,
)
from api.v1.permissions.application import (
    IsTutor,
    IsStudentTutor,
    IsInspector,
    IsStudent,
    IsOwnerOrInspectorOrTutor,
)
from api.v1.utils import calculate_score
from api.v1.filters.application import ApplicationFilter, QuotaFIlter, AppealFilter
from core.pagination import PageNumberPagination

from apps.application.models import (
    Application,
    Attempt,
    Question,
    Appeal,
    Criterion,
    Item,
    CriterionThrough,
    Quota,
)
from apps.user.models import Student, Inspector
import random


class AppealViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Appeal.objects.all()
    serializer_class = AppealSerializer
    pagination_class = PageNumberPagination
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppealFilter

    def get_serializer_class(self):
        if self.action == "create":
            return AppealCreateSerializer
        elif self.action == "approve":
            return AppealApproveSerializer
        return AppealSerializer
    
    def get_permissions(self):
        if self.action in ["approve_appeal"]:
            self.permission_classes = [permissions.IsAuthenticated, IsInspector]
        elif self.action in ["create"]:
            self.permission_classes = [permissions.IsAuthenticated, IsStudent]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsOwnerOrInspectorOrTutor]
        return super().get_permissions()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Appeal.objects.none()

        if self.request.user.is_superuser or self.request.user.is_staff:
            return self.queryset

        student = Student.objects.filter(user=self.request.user).first()
        if student:
            return self.queryset.filter(application__student=student)

        inspector = Inspector.objects.filter(user=self.request.user).first()
        if inspector:
            return self.queryset

        return Appeal.objects.none()

    def perform_create(self, serializer):
        student = Student.objects.filter(user=self.request.user.id).first()
        if Appeal.objects.filter(
            student=student,
            application=serializer.validated_data.get("application"),
        ).exists():
            raise serializers.ValidationError("Sizning arizangiz allaqachon mavjud.")

        application = serializer.validated_data.get("application")
        if not application or application.student != student:
            raise serializers.ValidationError("Sizning arizangiz topilmadi.")
        
        if application.is_rejected == True:
            raise serializers.ValidationError("Sizning arizangiz rad etilgan.")

        if not student:
            raise serializers.ValidationError(
                "Faqat talabalar appellatsiya yuborishi mumkin."
            )
        serializer.save(student=student)
        
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, *args, **kwargs):
        appeal = self.get_object()
        serializer = self.get_serializer(data=request.data, instance=appeal, partial=True)
        serializer.is_valid(raise_exception=True)
        appeal = serializer.save(resolved_at=timezone.now(), resolved_by=request.user)
        application = appeal.application
        application.is_revised = True
        application.save()
        return Response(serializer.data, status=200)


class ApplicationViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Application.objects.all()
    serializer_class = ApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApplicationFilter
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action in [
            "approve_social_score",
            "approve_education_score",
            "approve",
        ]:
            self.permission_classes = [permissions.IsAuthenticated, IsInspector]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Application.objects.none()

        if self.request.user.is_superuser or self.request.user.is_staff:
            return self.queryset

        if hasattr(self.request.user, "tutor_profile"):
            groups = self.request.user.tutor_profile.group.all().values_list(
                "name", flat=True
            )
            return Application.objects.filter(student__group__in=groups)

        if hasattr(self.request.user, "inspector_profile"):
            return Application.objects.all()

        student = Student.objects.filter(user=self.request.user).first()
        if student:
            return self.queryset.filter(student=student)

        return Application.objects.none()

    def perform_create(self, serializer):
        student = Student.objects.filter(user=self.request.user).first()
        if not student:
            raise serializers.ValidationError("Faqat talabalar ariza yuborishi mumkin.")
        type = serializer.validated_data.get("type", "standard")
        if student.gpa < 3.5 and type == "standard":
            raise serializers.ValidationError(
                "GPA bali 3.5 dan kam bo'lgan talabalar ariza yubora olmaydi."
            )
        if student.gpa < 3.3 and type == "preferred":
            raise serializers.ValidationError(
                "Ushbu turdagi arizani yuborish uchun GPA bali 3.3 dan yuqori bo'lishi kerak."
            )
        if Application.objects.filter(
            student=student,
            type=type,
        ).exists():
            raise serializers.ValidationError("Sizning arizangiz allaqachon mavjud.")
        instance = serializer.save(student=student)
        if instance.type == "standard":
            criterions = Criterion.objects.filter(preferred=False)
        else:
            criterions = Criterion.objects.filter(preferred=True)
        for criterion in criterions:
            item = Item.objects.create()
            CriterionThrough.objects.create(
                criterion=criterion, item=item, application=instance
            )
        return instance

    def create(self, request, *args, **kwargs):
        return Response("Ariza topshirish tugallandi.", status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        response = ApplicationSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(response.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        application = self.get_object()
        if (
            not application.is_education_score_approved
            or not application.is_social_score_approved
        ):
            return Response(
                {"detail": "Ta'lim bali yoki ijtimoiy ball tasdiqlanmagan."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student = application.student
        others = Application.objects.filter(student=student, is_approved=True).exclude(
            id=pk
        )

        for other in others:
            other.is_approved = False
            other.save()

        application.is_approved = True
        application.save()

        student.social_score = application.score
        student.save()
        return Response({"status": "approved"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="education/approve")
    def approve_education_score(self, request, pk=None):
        application = self.get_object()
        student = application.student
        others = Application.objects.filter(
            student=student, is_education_score_approved=True
        ).exclude(id=pk)

        for other in others:
            other.is_education_score_approved = False
            other.save()

        application.is_education_score_approved = True
        application.save()
        return Response({"status": "approved"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="social/approve")
    def approve_social_score(self, request, pk=None):
        application = self.get_object()
        student = application.student
        others = Application.objects.filter(
            student=student, is_social_score_approved=True
        ).exclude(id=pk)

        for other in others:
            other.is_social_score_approved = False
            other.save()

        application.is_social_score_approved = True
        application.save()
        return Response({"status": "approved"}, status=status.HTTP_200_OK)


class AttemptViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Attempt.objects.all()
    serializer_class = AttemptCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    authentication_classes = [JWTCookieAuthentication, JWTAuthentication]
    student = None

    def get_serializer_class(self):
        if self.action == "create":
            return AttemptCreateSerializer
        elif self.action == "answer":
            return AnswerAttemptSerializer
        elif self.action == "complete_attempt":
            return None
        return AttemptSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Attempt.objects.none()

        if self.request.user.is_superuser or self.request.user.is_staff:
            return self.queryset

        self.student = Student.objects.filter(user=self.request.user).first()
        if self.student:
            return self.queryset.filter(student=self.student)

        return Attempt.objects.none()

    def perform_create(self, serializer):
        instance = serializer.save(student=self.student)
        all_questions = Question.objects.all()
        questions = random.sample(list(all_questions), 20)
        for question in questions:
            instance.answers.create(question=question)

        return instance

    def create(self, request, *args, **kwargs):
        self.student = Student.objects.filter(user=request.user).first()
        attempt = Attempt.objects.filter(
            student=self.student,
            is_completed=False,
            created_at__gt=timezone.now() - timedelta(minutes=30),
        ).first()
        if attempt:
            response = AttemptSerializer(attempt, context=self.get_serializer_context())
            headers = self.get_success_headers(response.data)
            return Response(
                response.data, status=status.HTTP_201_CREATED, headers=headers
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data.pop("application_id", None)
        instance = self.perform_create(serializer)
        application.test = instance
        application.save()

        response = AttemptSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(response.data)
        return Response(response.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="answer")
    def answer(self, request, pk=None):
        attempt = self.get_object()
        if (
            attempt.is_completed
            or attempt.created_at + timedelta(minutes=30) < timezone.now()
        ):
            return Response(
                {"detail": "Ushbu urinish tugatilgan yoki vaqt tugagan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt_item = attempt.answers.filter(
            question=serializer.validated_data["question"]
        ).first()
        if not attempt_item:
            return Response(
                {"detail": "Savol ushbu topshiriqqa tegishli emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt_item.answers.set(serializer.validated_data.get("answers", []))
        attempt_item.save()

        return Response({"detail": "Javob qabul qilindi"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete_attempt(self, request, pk=None):
        attempt = self.get_object()
        if (
            not attempt
            or attempt.is_completed
            or attempt.created_at + timedelta(minutes=30) < timezone.now()
        ):
            return Response(
                {"detail": "Topshiriq topilmadi."}, status=status.HTTP_404_NOT_FOUND
            )

        calculate_score(attempt)

        serializer = AttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApplicationFileUploadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrInspectorOrTutor]
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    serializer_class = ApplicationFileUploadSerializer

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'inspector_profile'):
            return Response("Arizalarni tahrirlash yakunlangan.", status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data.get("file")
        if not file:
            return Response(
                {"detail": "Fayl yuborilmagan."}, status=status.HTTP_400_BAD_REQUEST
            )

        application_id = kwargs.get("application_id")
        criterion_id = kwargs.get("criterion_id")
        application = Application.objects.filter(id=application_id).first()
        criterion = application.criteria.filter(id=criterion_id).first()
        if application.is_social_score_approved:
            return Response(
                {"detail": "Ijtimoiy ball tasdiqlangan, fayl yuklash mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not application or not criterion:
            return Response(
                {"detail": "Ariza yoki mezon topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if (
            not criterion.criterion_through.first().criterion.student_uploadable
            and hasattr(request.user, "student_profile")
        ):
            return Response(
                {"detail": "Ushbu mezon uchun fayl yuklash mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        criterion.file = file
        criterion.uploaded_by = request.user
        criterion.uploaded_at = timezone.now()
        criterion.save()

        return Response(
            {"detail": "Fayl muvaffaqiyatli yuklandi."}, status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        if not hasattr(request.user, 'inspector_profile'):
            return Response("Arizalarni tahrirlash yakunlangan.", status=status.HTTP_400_BAD_REQUEST)

        application_id = kwargs.get("application_id")
        criterion_id = kwargs.get("criterion_id")
        application = Application.objects.filter(id=application_id).first()
        criterion = application.criteria.filter(id=criterion_id).first()
        if application.is_social_score_approved:
            return Response(
                {"detail": "Ijtimoiy ball tasdiqlangan, fayl o'chirish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not application or not criterion:
            return Response(
                {"detail": "Ariza yoki mezon topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        criterion.file = None
        criterion.uploaded_by = None
        criterion.save()

        return Response(
            {"detail": "Fayl muvaffaqiyatli o'chirildi."}, status=status.HTTP_200_OK
        )


class ApplicationCriterionScoreView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsInspector | IsStudentTutor]
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    serializer_class = ApplicationCriterionScoreSerializer

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'inspector_profile'):
            return Response("Arizalarni tahrirlash yakunlangan.", status=status.HTTP_400_BAD_REQUEST)

        application_id = kwargs.get("application_id")
        criterion_id = kwargs.get("criterion_id")
        application = Application.objects.filter(id=application_id).first()
        criterion = application.criteria.filter(id=criterion_id).first()

        if application.is_social_score_approved:
            return Response(
                {
                    "detail": "Ijtimoiy ball tasdiqlangan, ballarni yangilash mumkin emas."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not application or not criterion:
            return Response(
                {"detail": "Ariza yoki mezon topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        score = serializer.validated_data.get("score")

        if score > criterion.criterion_through.first().criterion.max_score:
            return Response(
                {"detail": "Belgilangan chegaradan ko'proq ball berish mumkin emas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        criterion.score = score
        criterion.save()

        return Response(
            {"detail": "Ballar muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK
        )


class ApplicationExportExcelView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsInspector)
    authentication_classes = [JWTAuthentication, JWTCookieAuthentication]
    queryset = (
        Application.objects.filter(is_rejected=False)
        .annotate(created_date=TruncDate("created_at"))
        .annotate(
            raw_social=Sum("criteria__score") + Coalesce(F("test__score"), Value(0))
        )
        .annotate(social=F("raw_social") / 5)
        .annotate(total=F("student__education_score") + F("social"))
        .annotate(
            type_=Case(
                When(type="standard", then=Value("Oddiy")),
                When(type="preferred", then=Value("Imtiyozli")),
            )
        )
        .order_by(
            "student__faculty",
            "student__speciality",
            "student__group",
            "student__level",
            "type",
        )
    )

    def get(self, request, *args, **kwargs):
        queryset = (
            self.get_queryset()
            .values(
                "student__user__username",
                "student__full_name",
                "created_date",
                "type_",
                "student__level",
                "student__faculty",
                "student__speciality",
                "student__group",
                "student__education_type",
                "student__education_language",
                "student__gpa",
                "raw_social",
                "student__education_score",
                "social",
                "total",
            )
            .distinct()
        )

        df = pd.DataFrame(list(queryset))
        df.rename(
            columns={
                "student__user__username": "ID",
                "student__full_name": "FIO",
                "created_date": "Sana",
                "type_": "Ariza Turi",
                "student__level": "Kurs",
                "student__faculty": "Fakultet",
                "student__speciality": "Yo'nalish",
                "student__group": "Guruh",
                "student__education_type": "Ta'lim Turi",
                "student__education_language": "Ta'lim Tili",
                "student__gpa": "GPA",
                "raw_social": "Ijtimoiy faollik indeksi ko'rsatkichi",
                "student__education_score": "Akademik ball",
                "social": "Ijtimoiy Ball",
                "total": "Jami Ball",
            },
            inplace=True,
        )
        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Students")
            worksheet = writer.sheets["Students"]
            for idx, col in enumerate(df):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(idx, idx, max_length)

            header_format = writer.book.add_format(
                {"bold": True, "font_color": "black", "bg_color": "#D9EAD3"}
            )
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="students.xlsx"'
        return response


class QuotaView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    queryset = Quota.objects.all()
    serializer_class = QuotaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = QuotaFIlter

    def get(self, request, *args, **kwargs):
        quotas = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(quotas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
