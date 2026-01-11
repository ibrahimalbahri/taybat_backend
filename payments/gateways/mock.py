from __future__ import annotations

# payments/gateways/mock.py
import uuid
from decimal import Decimal
from typing import Mapping

from .base import PaymentGateway, CaptureResult, RefundResult


class MockGateway(PaymentGateway):
    def capture(
        self,
        *,
        amount: Decimal,
        currency: str,
        payment_method_token: str,
        idempotency_key: str,
        metadata: Mapping[str, object],
    ) -> CaptureResult:
        # deterministic-ish: could hash idempotency_key; keep simple
        return CaptureResult(provider_ref=f"mock_charge_{uuid.uuid4().hex}")

    def refund(
        self,
        *,
        provider_ref: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        metadata: Mapping[str, object],
    ) -> RefundResult:
        return RefundResult(refund_ref=f"mock_refund_{uuid.uuid4().hex}")
