from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from drivers.models import DriverLocation
from orders.models import (
    Order,
    OrderDispatchState,
    OrderDriverSuggestion,
    OrderStatus,
    OrderType,
)
from orders.tasks import dispatch_match_loop, expire_order_suggestions
from users.models import Address, DriverProfile, DriverStatus, User, VehicleType


class DispatchTaskTests(TestCase):
    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            email="customer@example.com",
            name="Customer",
            phone="4000",
        )
        self.driver = User.objects.create_user(
            email="driver@example.com",
            name="Driver",
            phone="4001",
        )
        DriverProfile.objects.create(
            user=self.driver,
            status=DriverStatus.APPROVED,
            vehicle_type=VehicleType.BIKE,
            accepts_food=False,
            accepts_shipping=True,
            accepts_taxi=False,
            is_online=True,
        )
        DriverLocation.objects.create(
            driver=self.driver,
            lat=Decimal("24.7136"),
            lng=Decimal("46.6753"),
        )

        self.pickup = Address.objects.create(
            user=self.customer,
            label="pickup",
            lat=Decimal("24.7136"),
            lng=Decimal("46.6753"),
            full_address="Pickup Address",
            street_name="Pickup St",
            house_number="1",
            city="City",
            postal_code="00000",
            country="Country",
        )
        self.dropoff = Address.objects.create(
            user=self.customer,
            label="dropoff",
            lat=Decimal("24.7200"),
            lng=Decimal("46.6800"),
            full_address="Dropoff Address",
            street_name="Dropoff St",
            house_number="2",
            city="City",
            postal_code="00000",
            country="Country",
        )

        self.order = Order.objects.create(
            order_type=OrderType.SHIPPING,
            customer=self.customer,
            status=OrderStatus.SEARCHING_FOR_DRIVER,
            total_amount=Decimal("10.00"),
            pickup_address=self.pickup,
            dropoff_address=self.dropoff,
        )

    @override_settings(
        DISPATCH_ACCEPTANCE_WINDOW_SECONDS=60,
        DISPATCH_SUGGESTION_LIMIT=5,
        DISPATCH_MAX_CYCLES=3,
        DISPATCH_RETRY_DELAY_SECONDS=10,
        DISPATCH_LOCATION_STALE_SECONDS=60,
    )
    @patch("orders.tasks.send_dispatch_offer")
    @patch("orders.tasks.expire_order_suggestions.apply_async")
    def test_dispatch_match_loop_creates_suggestions(
        self,
        mock_apply_async,
        mock_send_dispatch_offer,
    ) -> None:
        dispatch_match_loop()

        suggestions = OrderDriverSuggestion.objects.filter(order=self.order)
        self.assertEqual(suggestions.count(), 1)
        suggestion = suggestions.first()
        assert suggestion is not None
        self.assertEqual(suggestion.driver_id, self.driver.id)
        self.assertEqual(suggestion.status, OrderDriverSuggestion.SuggestionStatus.SENT)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.DRIVER_NOTIFICATION_SENT)

        state = OrderDispatchState.objects.get(order=self.order)
        self.assertEqual(state.cycle, 1)
        self.assertTrue(state.is_active)

        mock_apply_async.assert_called_once()
        mock_send_dispatch_offer.assert_called_once()

    @override_settings(DISPATCH_LOCATION_STALE_SECONDS=60)
    @patch("orders.tasks.send_dispatch_offer")
    @patch("orders.tasks.expire_order_suggestions.apply_async")
    def test_dispatch_skips_when_pending_suggestion_exists(
        self,
        mock_apply_async,
        mock_send_dispatch_offer,
    ) -> None:
        OrderDriverSuggestion.objects.create(
            order=self.order,
            driver=self.driver,
            distance_at_time=Decimal("1.0"),
            cycle=1,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
            expires_at=timezone.now() + timedelta(seconds=60),
        )
        dispatch_match_loop()

        self.assertEqual(OrderDriverSuggestion.objects.filter(order=self.order).count(), 1)
        mock_apply_async.assert_not_called()
        mock_send_dispatch_offer.assert_not_called()

    def test_expire_order_suggestions_marks_expired(self) -> None:
        state = OrderDispatchState.objects.create(order=self.order, cycle=1)
        suggestion = OrderDriverSuggestion.objects.create(
            order=self.order,
            driver=self.driver,
            distance_at_time=Decimal("1.0"),
            cycle=1,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
        )
        self.order.status = OrderStatus.DRIVER_NOTIFICATION_SENT
        self.order.save(update_fields=["status"])

        expire_order_suggestions(self.order.id, 1)

        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, OrderDriverSuggestion.SuggestionStatus.EXPIRED)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.SEARCHING_FOR_DRIVER)

        state.refresh_from_db()
        self.assertIsNotNone(state.next_retry_at)
