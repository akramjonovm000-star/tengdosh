from django.dispatch import receiver
from django.db.models.signals import pre_save
from .models import Student

@receiver(pre_save, sender=Student)
def update_student_education_score(sender, instance, **kwargs):
    if instance.gpa:
        instance.education_score = instance.gpa * 16
        instance.score = round(instance.education_score + (instance.social_score / 5), 2)
