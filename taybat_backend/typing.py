from __future__ import annotations

from rest_framework.request import Request

from users.models import User


def get_authenticated_user(request: Request) -> User:
    user = request.user
    assert user and user.is_authenticated
    return user
