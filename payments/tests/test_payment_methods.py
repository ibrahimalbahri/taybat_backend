from typing import cast
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.response import Response
@pytest.mark.django_db
def test_customer_can_create_payment_method(customer_user):
    c = APIClient()
    c.force_authenticate(customer_user)

    url = "/api/customer/payment-methods/"
    payload = {
        "provider": "MOCK",
        "token": "pm_mock_123",
        "brand": "VISA",
        "last4": "4242",
        "exp_month": 12,
        "exp_year": 2030,
        "is_default": True
    }


    r = cast(Response, c.post(url, payload, format="json"))
    assert r.status_code == 201
    # assert r.data["last4"] == "4242"

@pytest.mark.django_db
def test_reject_pan_fields(customer_user):
    c = APIClient()
    c.force_authenticate(customer_user)

    url = "/api/customer/payment-methods/"
    payload = {"provider": "MOCK", "token": "pm_x", "pan": "4242424242424242"}
    r = cast(Response, c.post(url, payload, format="json"))

    assert r.status_code == 400
