from __future__ import annotations

from typing import Any, cast

import pytest
from rest_framework.test import APIClient
from loyalty.models import LoyaltyPoint, LoyaltySource
from rest_framework.response import Response


@pytest.mark.django_db
def test_admin_can_adjust_loyalty(admin_user: Any, customer_user: Any) -> None:
    c = APIClient()
    c.force_authenticate(admin_user)

    payload = {"user_id": customer_user.id, "points": 50, "note": "promo"}
    r = cast(Response, c.post("/api/admin/loyalty/adjust/", payload, format="json"))
    assert r.status_code == 200
    # lp = LoyaltyPoint.objects.get(id=r.data["id"])
    # assert lp.source == LoyaltySource.ADMIN_ADJUSTMENT
