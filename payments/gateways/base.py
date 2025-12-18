# payments/gateways/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureResult:
    provider_ref: str


@dataclass(frozen=True)
class RefundResult:
    refund_ref: str


class PaymentGateway(ABC):
    @abstractmethod
    def capture(self, *, amount, currency, payment_method_token, idempotency_key, metadata) -> CaptureResult:
        raise NotImplementedError

    @abstractmethod
    def refund(self, *, provider_ref, amount, currency, idempotency_key, metadata) -> RefundResult:
        raise NotImplementedError
