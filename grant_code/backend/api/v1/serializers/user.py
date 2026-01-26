from rest_framework import serializers, exceptions
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.utils.module_loading import import_string
from apps.user.models import User, Student, Inspector, Tutor


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(style={"input_type": "password"})

    def authenticate(self, username, password):
        if username and password:
            user = authenticate(username=username, password=password)
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(msg)
        return user

    @staticmethod
    def validate_auth_user_status(user):
        if not user.is_active:
            msg = _("User account is disabled.")
            raise exceptions.ValidationError(msg)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = self.authenticate(username, password)

        if not user:
            msg = _("Unable to log in with provided credentials.")
            raise exceptions.ValidationError(msg)

        # Did we get back an active user?
        self.validate_auth_user_status(user)

        attrs["user"] = user
        return attrs


class StudentSerializer(serializers.ModelSerializer):
    #application = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        view = self.context.get("view")
        StudentsView = import_string("api.v1.views.user.StudentsView")

        if not view or not isinstance(view, StudentsView):
            return obj.full_name

        user = self.context.get("request").user
        if (user.is_authenticated and obj.user == user) or not hasattr(
            user, "student_profile"
        ):
            print(hasattr(user, "student_profile"), user)
            return obj.full_name
        return "Natijalar e'lon qilingandan so'ng talalaning ism-sharifini ko'rishingiz mumkin."

    def get_application(self, obj):
        from api.v1.serializers.application import ApplicationSerializer
        from apps.application.models import Application

        application = Application.objects.filter(student=obj, is_approved=True).first()
        if application:
            return ApplicationSerializer(application, context=self.context).data
        return None

    def get_rank(self, obj):
        students = (
            Student.objects.filter(
                education_language=obj.education_language,
                faculty=obj.faculty,
                speciality=obj.speciality,
                education_type=obj.education_type,
                level=obj.level,
                education_form=obj.education_form,
            )
            .values_list("score", flat=True)
            .distinct()
            .order_by("-score")
        )
        for i, student in enumerate(students, start=1):
            if student == obj.score:
                return i
        return None

    class Meta:
        model = Student
        exclude = ("user",)


class StudentMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = (
            "id",
            "full_name",
            "gpa",
            "level",
            "group",
            "faculty",
            "speciality",
            "education_form",
            "education_type",
            "payment_type",
            "social_score",
            "education_score",
            "score",
        )
        read_only_fields = fields


class InspectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspector
        exclude = ("user",)


class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        exclude = ("user",)


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    def get_profile(self, obj):
        if hasattr(obj, "student_profile"):
            return StudentSerializer(obj.student_profile).data
        elif hasattr(obj, "inspector_profile"):
            return InspectorSerializer(obj.inspector_profile).data
        elif hasattr(obj, "tutor_profile"):
            return TutorSerializer(obj.tutor_profile).data
        return None

    def get_role(self, obj):
        if hasattr(obj, "student_profile"):
            return "student"
        elif hasattr(obj, "inspector_profile"):
            return "inspector"
        elif hasattr(obj, "tutor_profile"):
            return "tutor"
        return None

    class Meta:
        model = User
        fields = ("id", "username", "is_active", "is_staff", "profile", "role")
        read_only_fields = ("id", "username", "is_active", "is_staff")
