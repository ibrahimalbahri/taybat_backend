from __future__ import annotations

# loyalty/services/loyalty_service.py
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import transaction

from loyalty.models import LoyaltyPoint, LoyaltySource
from orders.models import Order
from users.models import User


class LoyaltyService:
    @staticmethod
    def _points_for_amount(amount: Decimal) -> int:
        # configurable: POINTS_PER_EUR, default 1 point per 1 EUR (rounded down)
        ppe = getattr(settings, "LOYALTY_POINTS_PER_EUR", 1)
        return int(Decimal(amount) * Decimal(ppe))

    @staticmethod
    def _already_issued(order: Order) -> bool:
        return LoyaltyPoint.objects.filter(order=order, source=LoyaltySource.ORDER).exists()

    @staticmethod
    @transaction.atomic
    def issue_for_order(*, order: Order) -> LoyaltyPoint | None:
        # Optionally restrict to FOOD only:
        only_food = getattr(settings, "LOYALTY_ONLY_FOOD", False)
        if only_food and getattr(order, "order_type", None) != "FOOD":
            return None

        # Issue only on COMPLETED (adjust if your canonical is DELIVERED)
        required_status = getattr(settings, "LOYALTY_ISSUE_ON_STATUS", "COMPLETED")
        if getattr(order, "status", None) != required_status:
            return None

        if LoyaltyService._already_issued(order):
            return None

        points = LoyaltyService._points_for_amount(Decimal(order.total_amount))
        if points <= 0:
            return None

        return LoyaltyPoint.objects.create(
            user=order.customer,  # adjust if your FK name differs
            points=points,
            source=LoyaltySource.ORDER,
            order=order,
            note="Auto-issued for completed order",
        )

    @staticmethod
    @transaction.atomic
    def reverse_for_order(*, order: Order, note: Optional[str] = None) -> LoyaltyPoint | None:
        issued = LoyaltyPoint.objects.filter(order=order, source=LoyaltySource.ORDER).first()
        if not issued:
            return None

        # prevent double reversals
        if LoyaltyPoint.objects.filter(order=order, source=LoyaltySource.REVERSAL).exists():
            return None

        return LoyaltyPoint.objects.create(
            user=issued.user,
            points=-abs(issued.points),
            source=LoyaltySource.REVERSAL,
            order=order,
            note=note or "Reversal due to refund/cancellation",
        )

    @staticmethod
    @transaction.atomic
    def admin_adjust(
        *,
        admin_user: User,
        user: User,
        points: int,
        note: Optional[str],
    ) -> LoyaltyPoint:
        if points == 0:
            raise ValueError("Points cannot be zero.")
        return LoyaltyPoint.objects.create(
            user=user,
            points=points,
            source=LoyaltySource.ADMIN_ADJUSTMENT,
            order=None,
            note=note,
            created_by=admin_user,
        )
