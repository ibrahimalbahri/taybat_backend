from rest_framework.permissions import BasePermission
from drivers.models import DriverStatus


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return (request.user and request.user.is_authenticated and request.user.has_role("customer"))

class IsDriver(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return (request.user and request.user.is_authenticated and request.user.has_role("driver"))

class IsSeller(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return (request.user and request.user.is_authenticated and request.user.has_role("seller"))

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return (request.user and request.user.is_authenticated and request.user.has_role("admin"))

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return (request.user and request.user.is_authenticated)


class IsApprovedDriver(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        if not (request.user and request.user.is_authenticated):
            return False
        if not request.user.has_role("driver"):
            return False
        try:
            return request.user.driver_profile.status == DriverStatus.APPROVED
        except Exception:
            return False
