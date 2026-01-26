import django_filters
from apps.user.models import Student


class StudentFilter(django_filters.FilterSet):
    full_name = django_filters.CharFilter(field_name='full_name', lookup_expr='icontains')
    speciality = django_filters.CharFilter(field_name='speciality', lookup_expr='icontains')
    education_form = django_filters.CharFilter(field_name='education_form', lookup_expr='icontains')
    level = django_filters.NumberFilter(field_name='level', lookup_expr='exact')
    group = django_filters.CharFilter(field_name='group', lookup_expr='icontains')
    faculty = django_filters.CharFilter(field_name='faculty', lookup_expr='icontains')
    education_type = django_filters.CharFilter(field_name='education_type', lookup_expr='icontains')
    education_language = django_filters.CharFilter(field_name='education_language', lookup_expr='icontains')
    payment_type = django_filters.CharFilter(field_name='payment_type', lookup_expr='icontains')
    gpa = django_filters.NumberFilter(field_name='gpa', lookup_expr='exact')
    
    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'speciality', 'education_form', 'level',
            'group', 'faculty', 'education_type', 'payment_type', 'gpa', 'education_language'
        ]
