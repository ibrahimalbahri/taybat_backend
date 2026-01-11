from __future__ import annotations

# payments/gateways/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class CaptureResult:
    provider_ref: str


@dataclass(frozen=True)
class RefundResult:
    refund_ref: str


class PaymentGateway(ABC):
    @abstractmethod
    def capture(
        self,
        *,
        amount: Decimal,
        currency: str,
        payment_method_token: str,
        idempotency_key: str,
        metadata: Mapping[str, object],
    ) -> CaptureResult:
        raise NotImplementedError

    @abstractmethod
    def refund(
        self,
        *,
        provider_ref: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        metadata: Mapping[str, object],
    ) -> RefundResult:
        raise NotImplementedError
