from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username field must be set')

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=100)
    
    gpa = models.FloatField()
    level = models.SmallIntegerField(default=1)
    group = models.CharField(max_length=50, blank=True, null=True)
    faculty = models.CharField(max_length=50, blank=True, null=True)
    speciality = models.CharField(max_length=50, blank=True, null=True)
    education_form = models.CharField(max_length=50, blank=True, null=True)
    education_type = models.CharField(max_length=50, blank=True, null=True)
    education_language = models.CharField(max_length=50, blank=True, null=True)
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    social_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)
    score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"


class Inspector(models.Model):
    TYPE_CHOICES = [
        ('education', 'Education'),
        ('social', 'Social'),
        ('special', 'Special'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='inspector_profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='special')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"


class Group(models.Model):
    name = models.CharField(max_length=50, unique=True)
    faculty = models.CharField(max_length=100, blank=True, null=True)
    speciality = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tutor_profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    group = models.ManyToManyField(Group, blank=True, related_name='tutors')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
