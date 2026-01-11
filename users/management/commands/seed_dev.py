from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import (
    AdminProfile,
    CustomerProfile,
    DriverProfile,
    DriverStatus,
    SellerProfile,
    User,
    VehicleType,
    Address,
)
from sellers.models import Restaurant, Category, Item, Coupon, RestaurantStatus
from orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    OrderType,
    OrderDriverSuggestion,
    ShippingPackage,
)


class Command(BaseCommand):
    help = "Seed dev data (users, roles, profiles, restaurant, menu, coupon)."

    def handle(self, *args: Any, **options: Any) -> None:
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
        admin_phone = os.getenv("SEED_ADMIN_PHONE", "9000000001")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "admin1234")

        seller_email = os.getenv("SEED_SELLER_EMAIL", "seller@example.com")
        seller_phone = os.getenv("SEED_SELLER_PHONE", "9000000002")
        seller_password = os.getenv("SEED_SELLER_PASSWORD", "seller1234")

        customer_email = os.getenv("SEED_CUSTOMER_EMAIL", "customer@example.com")
        customer_phone = os.getenv("SEED_CUSTOMER_PHONE", "9000000003")
        customer_password = os.getenv("SEED_CUSTOMER_PASSWORD", "customer1234")

        driver_email = os.getenv("SEED_DRIVER_EMAIL", "driver@example.com")
        driver_phone = os.getenv("SEED_DRIVER_PHONE", "9000000004")
        driver_password = os.getenv("SEED_DRIVER_PASSWORD", "driver1234")

        admin = self._get_or_create_user(
            email=admin_email,
            phone=admin_phone,
            name="Admin User",
            password=admin_password,
        )
        admin.add_role("admin")
        if not admin.is_staff:
            admin.is_staff = True
            admin.save(update_fields=["is_staff"])
        AdminProfile.objects.get_or_create(user=admin)

        seller = self._get_or_create_user(
            email=seller_email,
            phone=seller_phone,
            name="Seller User",
            password=seller_password,
        )
        seller.add_role("seller")
        SellerProfile.objects.get_or_create(user=seller)

        customer = self._get_or_create_user(
            email=customer_email,
            phone=customer_phone,
            name="Customer User",
            password=customer_password,
        )
        customer.add_role("customer")
        CustomerProfile.objects.get_or_create(user=customer)

        driver = self._get_or_create_user(
            email=driver_email,
            phone=driver_phone,
            name="Driver User",
            password=driver_password,
        )
        driver.add_role("driver")
        DriverProfile.objects.get_or_create(
            user=driver,
            defaults={
                "vehicle_type": VehicleType.BIKE,
                "status": DriverStatus.APPROVED,
                "accepts_food": True,
                "accepts_shipping": True,
                "accepts_taxi": True,
            },
        )

        Address.objects.get_or_create(
            user=customer,
            label="home",
            defaults={
                "lat": Decimal("24.7136"),
                "lng": Decimal("46.6753"),
                "full_address": "Seed Home Address",
                "street_name": "Main St",
                "house_number": "1",
                "city": "Riyadh",
                "postal_code": "00000",
                "country": "SA",
            },
        )
        pickup_address, _ = Address.objects.get_or_create(
            user=customer,
            label="pickup",
            defaults={
                "lat": Decimal("24.7200"),
                "lng": Decimal("46.6800"),
                "full_address": "Seed Pickup Address",
                "street_name": "Pickup St",
                "house_number": "10",
                "city": "Riyadh",
                "postal_code": "00001",
                "country": "SA",
            },
        )
        dropoff_address, _ = Address.objects.get_or_create(
            user=customer,
            label="dropoff",
            defaults={
                "lat": Decimal("24.7250"),
                "lng": Decimal("46.6850"),
                "full_address": "Seed Dropoff Address",
                "street_name": "Dropoff St",
                "house_number": "20",
                "city": "Riyadh",
                "postal_code": "00002",
                "country": "SA",
            },
        )

        restaurant, _ = Restaurant.objects.get_or_create(
            owner_user=seller,
            name="Seed Restaurant",
            defaults={
                "address": "Seed Address",
                "lat": Decimal("24.7136"),
                "lng": Decimal("46.6753"),
                "phone": "920000000",
                "status": RestaurantStatus.ACTIVE,
            },
        )

        category, _ = Category.objects.get_or_create(
            restaurant=restaurant,
            name="Burgers",
            defaults={"view_order": 1},
        )

        Item.objects.get_or_create(
            restaurant=restaurant,
            category=category,
            name="Classic Burger",
            defaults={
                "price": Decimal("25.00"),
                "description": "Seeded burger item",
                "view_order": 1,
                "is_available": True,
            },
        )
        burger = Item.objects.get(restaurant=restaurant, category=category, name="Classic Burger")

        now = timezone.now()
        Coupon.objects.get_or_create(
            restaurant=restaurant,
            code="SEED10",
            defaults={
                "title": "Seed 10% Off",
                "description": "Seed coupon",
                "percentage": 10,
                "min_price": Decimal("0.00"),
                "start_date": now,
                "end_date": now + timedelta(days=30),
                "is_active": True,
            },
        )

        self._seed_orders(
            customer=customer,
            driver=driver,
            restaurant=restaurant,
            burger=burger,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
        )

        self.stdout.write(self.style.SUCCESS("Seed data created/updated successfully."))

    def _get_or_create_user(
        self,
        *,
        email: str,
        phone: str,
        name: str,
        password: str,
    ) -> User:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "phone": phone,
                "name": name,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        else:
            updated_fields: list[str] = []
            if user.phone != phone:
                user.phone = phone
                updated_fields.append("phone")
            if user.name != name:
                user.name = name
                updated_fields.append("name")
            if updated_fields:
                user.save(update_fields=updated_fields)
        return user

    def _seed_orders(
        self,
        *,
        customer: User,
        driver: User,
        restaurant: Restaurant,
        burger: Item,
        pickup_address: Address,
        dropoff_address: Address,
    ) -> None:
        food_order, created = Order.objects.get_or_create(
            order_type=OrderType.FOOD,
            customer=customer,
            restaurant=restaurant,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            defaults={
                "status": OrderStatus.SEARCHING_FOR_DRIVER,
                "subtotal_amount": Decimal("25.00"),
                "discount_amount": Decimal("0.00"),
                "delivery_fee": Decimal("5.00"),
                "tip": Decimal("2.00"),
                "total_amount": Decimal("32.00"),
            },
        )
        if created:
            OrderItem.objects.create(
                order=food_order,
                item=burger,
                quantity=1,
                customizations=None,
            )
            OrderStatusHistory.objects.create(
                order=food_order,
                status=food_order.status,
            )
            OrderDriverSuggestion.objects.get_or_create(
                order=food_order,
                driver=driver,
                defaults={"distance_at_time": Decimal("2.5")},
            )

        shipping_order, created = Order.objects.get_or_create(
            order_type=OrderType.SHIPPING,
            customer=customer,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            defaults={
                "status": OrderStatus.PENDING,
                "subtotal_amount": Decimal("15.00"),
                "discount_amount": Decimal("0.00"),
                "delivery_fee": Decimal("8.00"),
                "tip": Decimal("0.00"),
                "total_amount": Decimal("23.00"),
                "requested_delivery_type": VehicleType.BIKE,
                "calculated_distance": Decimal("3.200"),
                "calculated_time": 900,
            },
        )
        if created:
            ShippingPackage.objects.create(
                order=shipping_order,
                size="M",
                weight=Decimal("2.50"),
                content="Seed package",
            )
            OrderStatusHistory.objects.create(
                order=shipping_order,
                status=shipping_order.status,
            )

        taxi_order, created = Order.objects.get_or_create(
            order_type=OrderType.TAXI,
            customer=customer,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            defaults={
                "status": OrderStatus.PENDING,
                "subtotal_amount": Decimal("12.00"),
                "discount_amount": Decimal("0.00"),
                "delivery_fee": Decimal("5.00"),
                "tip": Decimal("3.00"),
                "total_amount": Decimal("20.00"),
                "requested_vehicle_type": VehicleType.CAR,
                "calculated_distance": Decimal("4.000"),
                "calculated_time": 600,
            },
        )
        if created:
            OrderStatusHistory.objects.create(
                order=taxi_order,
                status=taxi_order.status,
            )
