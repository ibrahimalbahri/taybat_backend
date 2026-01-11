from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from restaurants.models import Coupon, CouponUsage
from orders.models import Order


class CouponError(Exception):
    pass


class CouponNotFound(CouponError):
    pass


class CouponNotActive(CouponError):
    pass


class CouponExpired(CouponError):
    pass


class CouponMinPriceNotMet(CouponError):
    pass


class CouponUsageLimitReached(CouponError):
    pass


@dataclass(frozen=True)
class CouponApplicationResult:
    coupon: Coupon
    discount_amount: Decimal
    final_total: Decimal


def _get_coupon_for_restaurant(*, restaurant_id: int, code: str) -> Coupon:
    coupon = (
        Coupon.objects
        .filter(restaurant_id=restaurant_id, code__iexact=code.strip())
        .first()
    )
    if not coupon:
        raise CouponNotFound("Invalid coupon code.")
    return coupon


def validate_coupon(
    *,
    restaurant_id: int,
    user_id: int,
    code: str,
    subtotal: Decimal,
) -> Coupon:
    """
    Validate coupon eligibility. Does not write any database rows.
    Use apply_coupon_to_order() to atomically record usage + attach to order.
    """
    now = timezone.now()
    coupon = _get_coupon_for_restaurant(restaurant_id=restaurant_id, code=code)

    if not coupon.is_active:
        raise CouponNotActive("Coupon is not active.")

    if now < coupon.start_date or now > coupon.end_date:
        raise CouponExpired("Coupon is not valid at this time.")

    if subtotal < coupon.min_price:
        raise CouponMinPriceNotMet("Order total does not meet the minimum price requirement.")

    # Check max_per_customer
    if coupon.max_per_customer is not None:
        per_customer_uses = CouponUsage.objects.filter(coupon=coupon, user_id=user_id).count()
        if per_customer_uses >= coupon.max_per_customer:
            raise CouponUsageLimitReached("You have reached the maximum uses for this coupon.")

    # Check max_total_users (unique users)
    if coupon.max_total_users is not None:
        unique_users = (
            CouponUsage.objects
            .filter(coupon=coupon)
            .values("user_id")
            .distinct()
            .count()
        )
        if unique_users >= coupon.max_total_users:
            # Note: this is conservative; it blocks once limit is reached.
            raise CouponUsageLimitReached("This coupon has reached its maximum number of users.")

    return coupon


def compute_discount(*, subtotal: Decimal, percentage: int) -> Decimal:
    if percentage <= 0:
        return Decimal("0.00")
    if percentage > 100:
        percentage = 100
    discount = (subtotal * Decimal(percentage) / Decimal(100)).quantize(Decimal("0.01"))
    return min(discount, subtotal)


@transaction.atomic
def apply_coupon_to_order(
    *,
    order: Order,
    user_id: int,
    code: str,
) -> CouponApplicationResult:
    """
    Atomically:
    - validates coupon
    - attaches it to the order
    - records CouponUsage
    Concurrency-safe via row lock on the coupon.
    """
    if not order.restaurant_id:
        raise CouponError("Coupons can only be applied to food orders with a restaurant.")

    # Lock coupon row so concurrent uses evaluate limits consistently.
    coupon = (
        Coupon.objects
        .select_for_update()
        .filter(restaurant_id=order.restaurant_id, code__iexact=code.strip())
        .first()
    )
    if not coupon:
        raise CouponNotFound("Invalid coupon code.")

    # Re-run validations while holding lock
    validate_coupon(
        restaurant_id=order.restaurant_id,
        user_id=user_id,
        code=code,
        subtotal=order.total_amount,
    )
    # Ensure subtotal_amount is set (important for older orders or partial flows)
    if order.subtotal_amount is None:
        order.subtotal_amount = order.total_amount

    discount = compute_discount(subtotal=order.subtotal_amount, percentage=coupon.percentage)

    # Final payable amount convention (recommended):
    # total_amount = subtotal - discount + delivery_fee + tip
    final_total = (order.subtotal_amount - discount + order.delivery_fee + order.tip).quantize(Decimal("0.01"))

    order.coupon = coupon
    order.discount_amount = discount
    order.total_amount = final_total

    order.save(update_fields=["coupon", "subtotal_amount", "discount_amount", "total_amount"])


    CouponUsage.objects.create(
        coupon=coupon,
        user_id=user_id,
        order=order,
    )

    return CouponApplicationResult(coupon=coupon, discount_amount=discount, final_total=final_total)
