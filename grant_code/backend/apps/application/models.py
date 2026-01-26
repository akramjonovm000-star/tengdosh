from django.db import models

# Create your models here.


class Application(models.Model):
    TYPE_CHOICES = (
        ("standard", "Standard"),
        ("preferred", "Preferred"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student = models.ForeignKey(
        'user.Student',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='standard',
    )
    criteria = models.ManyToManyField(
        'Item',
        through='CriterionThrough',
        related_name='applications',
        blank=True
    )
    test = models.ForeignKey(
        "Attempt",
        on_delete=models.CASCADE,
        related_name='applications',
        blank=True,
        null=True
    )
    description = models.TextField(blank=True, null=True)
    is_education_score_approved = models.BooleanField(default=False)
    is_social_score_approved = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    is_revised = models.BooleanField(default=False)
    file_url = models.URLField(
        max_length=200,
        blank=True,
        null=True
    )

    @property
    def score(self):
        return self.education_score + (self.social_score / 5)
    
    @property
    def education_score(self):
        return self.student.education_score if self.student else 0

    @property
    def social_score(self):
        return sum(item.score for item in self.criteria.all()) + (self.test.score if self.test and self.test.is_completed else 0)

    def __str__(self):
        return f"{self.student} - #{self.id}"

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['created_at']


class Criterion(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    max_score = models.PositiveIntegerField(default=0)
    preferred = models.BooleanField(default=False)
    student_uploadable = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Criterion'
        verbose_name_plural = 'Criteria'
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    file = models.FileField(
        upload_to='applications/files/', blank=True, null=True)
    score = models.FloatField(default=0)
    uploaded_by = models.ForeignKey(
        'user.User',
        on_delete=models.CASCADE,
        related_name='files',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Application Item'
        verbose_name_plural = 'Application Items'
        ordering = ['score', 'uploaded_at']

    def __str__(self):
        return f"{self.pk} - {self.score}"


class CriterionThrough(models.Model):
    criterion = models.ForeignKey(
        Criterion,
        on_delete=models.CASCADE,
        related_name='criterion_through'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='criterion_through'
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='criterion_throughs'
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Criterion Through'
        verbose_name_plural = 'Criterion Throughs'
        unique_together = ('application', 'item')


class Answer(models.Model):
    text = models.TextField()

    class Meta:
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        ordering = ['id']


class Question(models.Model):
    text = models.TextField()
    answers = models.ManyToManyField(
        'Answer',
        related_name='questions',
        blank=True
    )
    is_multiple_choice = models.BooleanField(default=False)
    variants = models.ManyToManyField(
        'Answer',
        related_name='variant_questions',
        blank=True
    )

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['id']


class AttemptItem(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempt_items'
    )
    answers = models.ManyToManyField(
        Answer,
        related_name='attempt_items'
    )
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = 'Attempt Item'
        verbose_name_plural = 'Attempt Items'


class Attempt(models.Model):
    answers = models.ManyToManyField(
        AttemptItem,
        related_name='attempts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    student = models.ForeignKey(
        'user.Student',
        on_delete=models.CASCADE,
        related_name='attempts'
    )

    class Meta:
        verbose_name = 'Attempt'
        verbose_name_plural = 'Attempts'
        ordering = ['created_at']


class Appeal(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='appeals'
    )
    reason = models.TextField()
    response = models.TextField(blank=True, null=True)
    response_file = models.FileField(
        upload_to='appeals/responses/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(null=True, blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        'user.User',
        on_delete=models.SET_NULL,
        related_name='resolved_appeals',
        blank=True,
        null=True
    )
    student = models.ForeignKey(
        'user.Student',
        on_delete=models.CASCADE,
        related_name='appeals'
    )

    class Meta:
        verbose_name = 'Appeal'
        verbose_name_plural = 'Appeals'
        ordering = ['created_at']

    def __str__(self):
        return f"Appeal for {self.application} - Resolved: {self.resolved}"


class Quota(models.Model):
    speciality = models.CharField(max_length=100)
    education_type = models.CharField(max_length=100)
    education_language = models.CharField(max_length=100)
    level = models.IntegerField()
    complete_quota = models.IntegerField()
    incomplete_quota = models.IntegerField()
    quota = models.IntegerField()
    
    def __str__(self):
        return f"{self.education_type} - {self.education_language} - Level {self.level} - {self.speciality}"

    class Meta:
        verbose_name = 'Quota'
        verbose_name_plural = 'Quotas'
        unique_together = ('speciality', 'education_type', 'education_language', 'level')
