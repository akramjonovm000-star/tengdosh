from rest_framework.permissions import BasePermission


class IsApplicationOwner(BasePermission):
    """
    Custom permission to only allow owners of an application to access it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsStudent(BasePermission):
    """
    Custom permission to only allow students to access certain views.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(
            request.user, "student_profile"
        )


class IsInspector(BasePermission):
    """
    Custom permission to only allow inspectors to access certain views.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(
            request.user, "inspector_profile"
        )


class IsTutor(BasePermission):
    """
    Custom permission to only allow tutors to access certain views.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, "tutor_profile")

class IsStudentTutor(BasePermission):
    """
    Custom permission to allow access to the student or a tutor from the same faculty.
    """

    def has_object_permission(self, request, view, obj):
        return obj.student == request.user or (
            hasattr(request.user, "tutor_profile")
            and request.user.tutor_profile.faculty == obj.student.faculty
        )


class IsOwnerOrInspectorOrTutor(BasePermission):
    """
    Custom permission to allow access to the owner of the application,
    or an inspector or tutor.
    """

    def has_object_permission(self, request, view, obj):
        return obj.student == request.user or (
            hasattr(request.user, "inspector_profile")
            or (
                hasattr(request.user, "tutor_profile")
                and request.user.tutor_profile.faculty == obj.student.faculty
            )
        )
