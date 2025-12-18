# payments/gateways/selector.py
from django.conf import settings
from .mock import MockGateway

def get_gateway():
    # Later: if settings.PAYMENTS_PROVIDER == "STRIPE": return StripeGateway(...)
    return MockGateway()
