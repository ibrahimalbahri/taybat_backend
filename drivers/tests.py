from __future__ import annotations

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from drivers.models import DriverProfile, DriverStatus, VehicleType
from orders.models import Order, OrderDriverSuggestion, OrderStatus, OrderType
from users.models import Address, CustomerProfile, User


class DriverOrderAcceptanceTests(APITestCase):
    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            email="customer@example.com",
            name="Customer",
            phone="4000",
        )
        self.customer.add_role("customer")
        CustomerProfile.objects.get_or_create(user=self.customer)

        self.driver = User.objects.create_user(
            email="driver@example.com",
            name="Driver",
            phone="4001",
        )
        self.driver.add_role("driver")
        self.driver.add_role("customer")
        DriverProfile.objects.create(
            user=self.driver,
            status=DriverStatus.PENDING,
            vehicle_type=VehicleType.BIKE,
            accepts_food=False,
            accepts_shipping=True,
            accepts_taxi=False,
        )

        self.pickup = Address.objects.create(
            user=self.customer,
            label="pickup",
            lat=0,
            lng=0,
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
            lat=0,
            lng=0,
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
            total_amount=10,
            pickup_address=self.pickup,
            dropoff_address=self.dropoff,
        )
        OrderDriverSuggestion.objects.create(
            order=self.order,
            driver=self.driver,
            distance_at_time=1,
        )

    def test_pending_driver_cannot_accept(self) -> None:
        url = reverse("driver-accept-order")
        self.client.force_authenticate(user=self.driver)
        response = self.client.post(url, {"order_id": self.order.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_driver_can_accept(self) -> None:
        profile = self.driver.driver_profile
        profile.status = DriverStatus.APPROVED
        profile.save(update_fields=["status"])

        url = reverse("driver-accept-order")
        self.client.force_authenticate(user=self.driver)
        response = self.client.post(url, {"order_id": self.order.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.ACCEPTED)
        self.assertEqual(self.order.driver_id, self.driver.id)
        self.assertTrue(self.driver.has_role("customer"))

    def test_driver_cannot_accept_own_order(self) -> None:
        own_order = Order.objects.create(
            order_type=OrderType.SHIPPING,
            customer=self.driver,
            status=OrderStatus.SEARCHING_FOR_DRIVER,
            total_amount=10,
            pickup_address=self.pickup,
            dropoff_address=self.dropoff,
        )
        OrderDriverSuggestion.objects.create(
            order=own_order,
            driver=self.driver,
            distance_at_time=1,
        )

        profile = self.driver.driver_profile
        profile.status = DriverStatus.APPROVED
        profile.save(update_fields=["status"])

        url = reverse("driver-accept-order")
        self.client.force_authenticate(user=self.driver)
        response = self.client.post(url, {"order_id": own_order.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
