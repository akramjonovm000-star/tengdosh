from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from apps.application.models import (
    Application,
    Item,
    Criterion,
    CriterionThrough,
    Attempt,
    AttemptItem,
    Question,
    Answer,
    Appeal,
    Quota
)
from apps.user.models import Student
from api.v1.utils import calculate_score
from api.v1.serializers.user import StudentMinimalSerializer


class AttemptCreateSerializer(serializers.ModelSerializer):
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        required=True
    )

    def validate(self, attrs):
        user = self.context["request"].user
        student = Student.objects.filter(user=user).first()

        if not student:
            raise serializers.ValidationError(
                "Talaba maydoni bo'sh bo'lishi mumkin emas."
            )
        application = attrs.get("application_id")
        if not application or application.student != student or application.test:
            raise serializers.ValidationError(
                "Siz ushbu ariza uchun test topshirishingiz mumkin emas."
            )

        uncompleted_attempts = Attempt.objects.filter(
            student=student,
            is_completed=False,
            created_at__gte=timezone.now() - timedelta(minutes=30),
        )
        if uncompleted_attempts.exists():
            raise serializers.ValidationError(
                "Sizda tugallanmagan test topshirig'i mavjud."
            )
        student_attempts = Attempt.objects.filter(
            student=student
        )

        if student_attempts:
            raise serializers.ValidationError(
                "Siz allaqachon test topshirdingiz."
            )
        return super().validate(attrs)

    class Meta:
        model = Attempt
        fields = ("application_id",)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    variants = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        exclude = ("answers",)


class AttemptItemSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = AttemptItem
        exclude = ("is_correct",)


class AttemptItemWithCorrectSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    is_correct = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttemptItem
        fields = ("question", "answers", "is_correct")


class AnswerAttemptSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=True,
    )
    answers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Answer.objects.all(),
    )

    def validate(self, attrs):
        question = attrs.get("question")
        answers = attrs.get("answers", [])

        if not question:
            raise serializers.ValidationError(
                "Savol maydoni bo'sh bo'lishi mumkin emas."
            )

        if not answers:
            raise serializers.ValidationError(
                "Javoblar maydoni bo'sh bo'lishi mumkin emas."
            )

        for answer in answers:
            if answer not in question.variants.all():
                raise serializers.ValidationError(
                    f"Berilgan javoblar savolga mos kelmaydi."
                )
        return attrs

    class Meta:
        model = AttemptItem
        fields = ("question", "answers")


class AttemptSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    def get_answers(self, obj):
        """
        Returns a list of AttemptItemSerializer for the answers related to the attempt.
        """
        if obj.is_completed:
            return AttemptItemWithCorrectSerializer(obj.answers.all(), many=True, context=self.context).data
        else:
            return AttemptItemSerializer(obj.answers.all(), many=True, context=self.context).data

    class Meta:
        model = Attempt
        fields = (
            "id",
            "answers",
            "created_at",
            "closed_at",
            "score",
            "student",
        )


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Criterion
        fields = "__all__"


class CriterionThroughSerializer(serializers.ModelSerializer):
    criterion = CriterionSerializer(read_only=True)
    item = ItemSerializer(read_only=True)

    class Meta:
        model = CriterionThrough
        fields = ("criterion", "item", "description")


class ApplicationSerializer(serializers.ModelSerializer):
    criteria = serializers.SerializerMethodField()
    test = serializers.SerializerMethodField()
    social_score = serializers.SerializerMethodField()
    education_score = serializers.SerializerMethodField()
    student = StudentMinimalSerializer(read_only=True)

    def get_criteria(self, obj):
        criterions = obj.criterion_throughs.all().order_by("criterion__id")
        return CriterionThroughSerializer(criterions, many=True, context=self.context).data

    def get_test(self, obj):
        test = obj.test
        if test:
            if not test.is_completed and test.created_at < timezone.now() - timedelta(minutes=30):
                calculate_score(test)
            return AttemptSerializer(test, context=self.context).data
        return None

    def get_social_score(self, obj):
        score = 0
        test = obj.test
        if test and test.is_completed:
            score += test.score
        if obj.criteria.exists():
            for criterion in obj.criteria.all():
                score += criterion.score
        return score

    def get_education_score(self, obj):
        if obj.student:
            return obj.student.education_score

    class Meta:
        model = Application
        fields = "__all__"


class ApplicationCreateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=Application.TYPE_CHOICES, default=Application.TYPE_CHOICES[0][0]
    )

    class Meta:
        model = Application
        fields = ("type",)


class ApplicationFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        if not value.name.lower().endswith(('.pdf', '.docx', '.jpg', '.jpeg', '.png', '.doc', '.heic')):
            raise serializers.ValidationError(
                "Fayl turi noto'g'ri. PDF, DOCX, DOC, JPG, JPEG, PNG fayllari qabul qilinadi.")
        return value


class ApplicationCriterionScoreSerializer(serializers.Serializer):
    score = serializers.FloatField(required=True)

    def validate_score(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError(
                "Ballar 0 dan 20 gacha bo'lishi kerak.")
        return value


class AppealCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ("application", "reason")
        read_only_fields = ("id", "created_at", "updated_at", "student")


class AppealSerializer(serializers.ModelSerializer):
    student = StudentMinimalSerializer(read_only=True)
    application = ApplicationSerializer(read_only=True)

    class Meta:
        model = Appeal
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "student", "application")


class AppealApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ("response", "response_file", "resolved")
        read_only_fields = ("id", "created_at", "updated_at", "student", "application")


class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
        fields = "__all__"