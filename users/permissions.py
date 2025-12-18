from rest_framework.permissions import BasePermission
from users.models import UserRole


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.CUSTOMER)

class IsDriver(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.DRIVER)

class IsSeller(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.SELLER)

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if getattr(request.user, "is_superuser", False):
            return True
        return bool(request.user and request.user.is_authenticated)