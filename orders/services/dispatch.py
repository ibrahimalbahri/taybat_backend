from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Iterable

from django.conf import settings
from django.utils import timezone

from orders.models import Order
from orders.services.eligibility import is_driver_eligible_for_order
from orders.services.pricing import haversine_distance
from users.models import DriverProfile, DriverStatus


@dataclass(frozen=True)
class DriverCandidate:
    driver_id: int
    distance_km: Decimal


def select_driver_candidates(order: Order, exclude_driver_ids: Iterable[int]) -> list[DriverCandidate]:
    now = timezone.now()
    stale_cutoff = now - timedelta(seconds=settings.DISPATCH_LOCATION_STALE_SECONDS)

    profiles = (
        DriverProfile.objects.select_related("user")
        .filter(
            status=DriverStatus.APPROVED,
            is_online=True,
            user__driver_location__updated_at__gte=stale_cutoff,
        )
        .exclude(user_id__in=exclude_driver_ids)
        .exclude(user_id=order.customer_id)
    )

    candidates: list[DriverCandidate] = []
    pickup_lat = order.pickup_address.lat
    pickup_lng = order.pickup_address.lng

    for profile in profiles:
        if not is_driver_eligible_for_order(driver_profile=profile, order=order):
            continue
        location = profile.user.driver_location
        distance = haversine_distance(pickup_lat, pickup_lng, location.lat, location.lng)
        candidates.append(DriverCandidate(driver_id=profile.user_id, distance_km=distance))

    candidates.sort(key=lambda item: item.distance_km)
    return candidates
