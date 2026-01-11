from __future__ import annotations

# payments/gateways/selector.py
from django.conf import settings

from .base import PaymentGateway
from .mock import MockGateway

def get_gateway() -> PaymentGateway:
    # Later: if settings.PAYMENTS_PROVIDER == "STRIPE": return StripeGateway(...)
    return MockGateway()
