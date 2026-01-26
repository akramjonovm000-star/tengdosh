import django_filters
from apps.application.models import Application, Quota, Appeal


class ApplicationFilter(django_filters.FilterSet):
    is_approved = django_filters.BooleanFilter(field_name="is_approved")
    is_rejected = django_filters.BooleanFilter(field_name="is_rejected")
    is_revised = django_filters.BooleanFilter(field_name="is_revised")
    type = django_filters.CharFilter(field_name="type")
    speciality = django_filters.CharFilter(field_name='student__speciality')
    education_form = django_filters.CharFilter(field_name='student__education_form')
    level = django_filters.NumberFilter(field_name='student__level')
    group = django_filters.CharFilter(field_name='student__group')
    faculty = django_filters.CharFilter(field_name='student__faculty')
    education_type = django_filters.CharFilter(field_name='student__education_type')
    education_language = django_filters.CharFilter(field_name='student__education_language')

    class Meta:
        model = Application
        fields = [
            "id",
            "student",
            "is_approved",
            "is_rejected",
            "is_revised",
            "type",
            "speciality",
            "education_form",
            "level",
            "group",
            "faculty",
            "education_type",
            "education_language"
        ]

class AppealFilter(django_filters.FilterSet):
    resolved = django_filters.CharFilter(method='filter_resolved')
    type = django_filters.CharFilter(field_name="application__type")
    speciality = django_filters.CharFilter(field_name='application__student__speciality')
    education_form = django_filters.CharFilter(field_name='application__student__education_form')
    level = django_filters.NumberFilter(field_name='application__student__level')
    group = django_filters.CharFilter(field_name='application__student__group')
    faculty = django_filters.CharFilter(field_name='application__student__faculty')
    education_type = django_filters.CharFilter(field_name='application__student__education_type')
    education_language = django_filters.CharFilter(field_name='application__student__education_language')

    def filter_resolved(self, queryset, name, value):
        if value.lower() == "true":
            return queryset.filter(resolved=True)
        elif value.lower() == "false":
            return queryset.filter(resolved=False)
        elif value.lower() == "null":
            return queryset.filter(resolved__isnull=True)
        return queryset

    class Meta:
        model = Appeal
        fields = [
            "id",
            "student",
            "resolved",
            "type",
            "speciality",
            "education_form",
            "level",
            "group",
            "faculty",
            "education_type",
            "education_language"
        ]

class QuotaFIlter(django_filters.FilterSet):
    speciality = django_filters.CharFilter(field_name='speciality', lookup_expr='exact')
    education_type = django_filters.CharFilter(field_name='education_type')
    level = django_filters.NumberFilter(field_name='level')
    education_language = django_filters.CharFilter(field_name='education_language')

    class Meta:
        model = Quota
        fields = [
            "speciality",
            "education_type",
            "level",
            "education_language"
        ]