from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from notifications.services.push import send_dispatch_offer
from orders.models import (
    Order,
    OrderDispatchState,
    OrderDriverSuggestion,
    OrderStatus,
    OrderStatusHistory,
)
from orders.services.dispatch import select_driver_candidates


@shared_task
def dispatch_match_loop() -> None:
    now = timezone.now()
    orders = Order.objects.filter(
        status__in=[OrderStatus.SEARCHING_FOR_DRIVER, OrderStatus.DRIVER_NOTIFICATION_SENT],
        driver__isnull=True,
    ).select_related("pickup_address", "dropoff_address")

    for order in orders:
        with transaction.atomic():
            try:
                locked_order = Order.objects.select_for_update().get(pk=order.pk)
            except Order.DoesNotExist:
                continue

            state, _created = OrderDispatchState.objects.select_for_update().get_or_create(
                order=locked_order
            )

            if not state.is_active:
                continue

            if state.next_retry_at and state.next_retry_at > now:
                continue

            pending_exists = OrderDriverSuggestion.objects.filter(
                order=locked_order,
                status=OrderDriverSuggestion.SuggestionStatus.SENT,
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=now)
            ).exists()
            if pending_exists:
                continue

            if state.cycle >= settings.DISPATCH_MAX_CYCLES:
                state.is_active = False
                state.updated_at = now
                state.save(update_fields=["is_active", "updated_at"])
                continue

            exclude_driver_ids = OrderDriverSuggestion.objects.filter(
                order=locked_order
            ).values_list("driver_id", flat=True)
            candidates = select_driver_candidates(locked_order, exclude_driver_ids)

            if not candidates:
                state.next_retry_at = now + timedelta(
                    seconds=settings.DISPATCH_RETRY_DELAY_SECONDS
                )
                state.save(update_fields=["next_retry_at"])
                continue

            cycle = state.cycle + 1
            suggestion_limit = settings.DISPATCH_SUGGESTION_LIMIT
            acceptance_window = settings.DISPATCH_ACCEPTANCE_WINDOW_SECONDS
            expires_at = now + timedelta(seconds=acceptance_window)

            suggestions = [
                OrderDriverSuggestion(
                    order=locked_order,
                    driver_id=candidate.driver_id,
                    distance_at_time=candidate.distance_km,
                    cycle=cycle,
                    status=OrderDriverSuggestion.SuggestionStatus.SENT,
                    notified_at=now,
                    expires_at=expires_at,
                )
                for candidate in candidates[:suggestion_limit]
            ]
            OrderDriverSuggestion.objects.bulk_create(suggestions)

            state.cycle = cycle
            state.last_dispatched_at = now
            state.next_retry_at = now + timedelta(
                seconds=settings.DISPATCH_RETRY_DELAY_SECONDS
            )
            state.save(update_fields=["cycle", "last_dispatched_at", "next_retry_at"])

            if locked_order.status != OrderStatus.DRIVER_NOTIFICATION_SENT:
                locked_order.status = OrderStatus.DRIVER_NOTIFICATION_SENT
                locked_order.save(update_fields=["status"])
                OrderStatusHistory.objects.create(
                    order=locked_order,
                    status=OrderStatus.DRIVER_NOTIFICATION_SENT,
                )

            expire_order_suggestions.apply_async(
                args=[locked_order.id, cycle],
                countdown=acceptance_window,
            )

            send_dispatch_offer(
                order=locked_order,
                driver_ids=[candidate.driver_id for candidate in candidates[:suggestion_limit]],
            )


@shared_task
def expire_order_suggestions(order_id: int, cycle: int) -> None:
    now = timezone.now()
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return

        if order.driver_id:
            return

        try:
            state = OrderDispatchState.objects.select_for_update().get(order=order)
        except OrderDispatchState.DoesNotExist:
            return

        if state.cycle != cycle:
            return

        suggestions = OrderDriverSuggestion.objects.filter(
            order=order,
            cycle=cycle,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
        )
        if not suggestions.exists():
            return

        suggestions.update(
            status=OrderDriverSuggestion.SuggestionStatus.EXPIRED,
            responded_at=now,
        )

        if order.status == OrderStatus.DRIVER_NOTIFICATION_SENT:
            order.status = OrderStatus.SEARCHING_FOR_DRIVER
            order.save(update_fields=["status"])
            OrderStatusHistory.objects.create(
                order=order,
                status=OrderStatus.SEARCHING_FOR_DRIVER,
            )

        state.next_retry_at = now
        state.save(update_fields=["next_retry_at"])
