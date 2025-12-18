# payments/gateways/mock.py
import uuid
from .base import PaymentGateway, CaptureResult, RefundResult


class MockGateway(PaymentGateway):
    def capture(self, *, amount, currency, payment_method_token, idempotency_key, metadata) -> CaptureResult:
        # deterministic-ish: could hash idempotency_key; keep simple
        return CaptureResult(provider_ref=f"mock_charge_{uuid.uuid4().hex}")

    def refund(self, *, provider_ref, amount, currency, idempotency_key, metadata) -> RefundResult:
        return RefundResult(refund_ref=f"mock_refund_{uuid.uuid4().hex}")
