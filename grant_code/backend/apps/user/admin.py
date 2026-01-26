from django.contrib import admin
from django.contrib.auth.models import Group

from .models import User, Student, Inspector, Tutor, Group as StudentGroup
from rest_framework.authtoken.admin import TokenProxy

admin.site.unregister(Group)
admin.site.unregister(TokenProxy)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_active', 'is_staff')
    search_fields = ('username',)
    ordering = ('username',)
    list_filter = ('is_active', 'is_staff')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'gpa', 'level', 'group', 'faculty', 'speciality', 'education_form', 'education_type', 'payment_type')
    search_fields = ('user__username', 'full_name')
    ordering = ('user__username',)
    list_filter = ('level', 'faculty', 'speciality')


@admin.register(Inspector)
class InspectorAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name')
    search_fields = ('user__username', 'first_name', 'last_name')
    ordering = ('user__username',)


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name')
    search_fields = ('user__username', 'first_name', 'last_name')
    ordering = ('user__username',)
    list_filter = ('user',)

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name} ({obj.user.username})"
    full_name.short_description = 'Full Name'


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'speciality')
    search_fields = ('name', 'faculty', 'speciality')
    ordering = ('name',)
    list_filter = ('faculty', 'speciality')

    def __str__(self):
        return self.name