from __future__ import annotations

import logging

from notifications.models import DeviceToken
from orders.models import Order

logger = logging.getLogger(__name__)


def send_dispatch_offer(*, order: Order, driver_ids: list[int]) -> int:
    """
    Hook for sending push notifications to drivers for a dispatch offer.
    """
    tokens = DeviceToken.objects.filter(
        user_id__in=driver_ids,
        is_active=True,
    )
    token_count = tokens.count()
    logger.info(
        "Dispatch offer push queued for order=%s drivers=%s tokens=%s",
        order.id,
        len(driver_ids),
        token_count,
    )
    return token_count
