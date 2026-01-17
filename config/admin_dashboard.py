from __future__ import annotations

from admin_tools.dashboard import Dashboard, modules
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone


class StatsDashboardModule(modules.DashboardModule):
    title = "Platform Stats"
    template = "admin_tools/dashboard/modules/taybat_stats.html"

    def init_with_context(self, context) -> None:
        from drivers.models import DriverVerification, DriverVerificationStatus
        from orders.models import Order, OrderStatus, OrderType
        from payments.models import Transaction, TransactionStatus, TransactionType
        from sellers.models import Coupon, Item, Restaurant, RestaurantStatus
        from users.models import (
            AdminProfile,
            CustomerProfile,
            DriverProfile,
            DriverStatus,
            SellerProfile,
            User,
        )

        now = timezone.now()
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        order_qs = Order.objects.all()
        order_counts = order_qs.aggregate(
            total=Count("id"),
            today=Count("id", filter=Q(created_at__gte=start_today)),
            pending=Count("id", filter=Q(status=OrderStatus.PENDING)),
            searching=Count("id", filter=Q(status=OrderStatus.SEARCHING_FOR_DRIVER)),
            on_the_way=Count("id", filter=Q(status=OrderStatus.ON_THE_WAY)),
            completed=Count("id", filter=Q(status=OrderStatus.COMPLETED)),
            cancelled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
        )
        order_type_counts = order_qs.aggregate(
            food=Count("id", filter=Q(order_type=OrderType.FOOD)),
            shipping=Count("id", filter=Q(order_type=OrderType.SHIPPING)),
            taxi=Count("id", filter=Q(order_type=OrderType.TAXI)),
        )

        user_counts = User.objects.aggregate(
            total=Count("id"),
            verified=Count("id", filter=Q(is_verified=True)),
            active=Count("id", filter=Q(is_active=True)),
            staff=Count("id", filter=Q(is_staff=True)),
        )
        profile_counts = {
            "customers": CustomerProfile.objects.count(),
            "drivers": DriverProfile.objects.count(),
            "sellers": SellerProfile.objects.count(),
            "admins": AdminProfile.objects.count(),
        }
        driver_counts = DriverProfile.objects.aggregate(
            pending=Count("id", filter=Q(status=DriverStatus.PENDING)),
            approved=Count("id", filter=Q(status=DriverStatus.APPROVED)),
            rejected=Count("id", filter=Q(status=DriverStatus.REJECTED)),
            online=Count("id", filter=Q(is_online=True)),
        )

        restaurant_counts = Restaurant.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(status=RestaurantStatus.ACTIVE)),
            pending=Count("id", filter=Q(status=RestaurantStatus.PENDING)),
            inactive=Count("id", filter=Q(status=RestaurantStatus.INACTIVE)),
        )
        item_counts = Item.objects.aggregate(
            total=Count("id"),
            available=Count("id", filter=Q(is_available=True)),
        )
        coupon_counts = Coupon.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
        )

        txn_qs = Transaction.objects.all()
        txn_counts = txn_qs.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=TransactionStatus.PENDING)),
            succeeded=Count("id", filter=Q(status=TransactionStatus.SUCCEEDED)),
            failed=Count("id", filter=Q(status=TransactionStatus.FAILED)),
            cancelled=Count("id", filter=Q(status=TransactionStatus.CANCELLED)),
        )
        revenue_total = (
            txn_qs.filter(
                status=TransactionStatus.SUCCEEDED,
                type__in=[
                    TransactionType.PAYMENT,
                    TransactionType.TIP,
                    TransactionType.ADJUSTMENT,
                ],
            )
            .aggregate(
                total=Coalesce(
                    Sum("amount"),
                    0,
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
            .get("total")
        )
        refunds_total = (
            txn_qs.filter(
                status=TransactionStatus.SUCCEEDED,
                type=TransactionType.REFUND,
            )
            .aggregate(
                total=Coalesce(
                    Sum("amount"),
                    0,
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
            .get("total")
        )
        revenue_month = (
            txn_qs.filter(
                status=TransactionStatus.SUCCEEDED,
                created_at__gte=start_month,
                type__in=[
                    TransactionType.PAYMENT,
                    TransactionType.TIP,
                    TransactionType.ADJUSTMENT,
                ],
            )
            .aggregate(
                total=Coalesce(
                    Sum("amount"),
                    0,
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
            .get("total")
        )

        verification_counts = DriverVerification.objects.aggregate(
            pending=Count("id", filter=Q(status=DriverVerificationStatus.PENDING)),
            approved=Count("id", filter=Q(status=DriverVerificationStatus.APPROVED)),
            rejected=Count("id", filter=Q(status=DriverVerificationStatus.REJECTED)),
        )

        self.sections = [
            {
                "title": "Orders",
                "stats": [
                    {"label": "Total orders", "value": order_counts["total"]},
                    {"label": "Orders today", "value": order_counts["today"]},
                    {"label": "Pending", "value": order_counts["pending"]},
                    {"label": "Searching for driver", "value": order_counts["searching"]},
                    {"label": "On the way", "value": order_counts["on_the_way"]},
                    {"label": "Completed", "value": order_counts["completed"]},
                    {"label": "Cancelled", "value": order_counts["cancelled"]},
                ],
            },
            {
                "title": "Orders by Type",
                "stats": [
                    {"label": "Food", "value": order_type_counts["food"]},
                    {"label": "Shipping", "value": order_type_counts["shipping"]},
                    {"label": "Taxi", "value": order_type_counts["taxi"]},
                ],
            },
            {
                "title": "Payments",
                "stats": [
                    {"label": "Transactions total", "value": txn_counts["total"]},
                    {"label": "Succeeded", "value": txn_counts["succeeded"]},
                    {"label": "Pending", "value": txn_counts["pending"]},
                    {"label": "Failed", "value": txn_counts["failed"]},
                    {"label": "Cancelled", "value": txn_counts["cancelled"]},
                    {"label": "Revenue total", "value": revenue_total},
                    {"label": "Refunds total", "value": refunds_total},
                    {"label": "Revenue this month", "value": revenue_month},
                ],
            },
            {
                "title": "Users",
                "stats": [
                    {"label": "Total users", "value": user_counts["total"]},
                    {"label": "Verified users", "value": user_counts["verified"]},
                    {"label": "Active users", "value": user_counts["active"]},
                    {"label": "Staff users", "value": user_counts["staff"]},
                    {"label": "Customers", "value": profile_counts["customers"]},
                    {"label": "Drivers", "value": profile_counts["drivers"]},
                    {"label": "Sellers", "value": profile_counts["sellers"]},
                    {"label": "Admins", "value": profile_counts["admins"]},
                    {"label": "Drivers online", "value": driver_counts["online"]},
                ],
            },
            {
                "title": "Marketplace",
                "stats": [
                    {"label": "Restaurants", "value": restaurant_counts["total"]},
                    {"label": "Restaurants active", "value": restaurant_counts["active"]},
                    {"label": "Restaurants pending", "value": restaurant_counts["pending"]},
                    {"label": "Restaurants inactive", "value": restaurant_counts["inactive"]},
                    {"label": "Items", "value": item_counts["total"]},
                    {"label": "Items available", "value": item_counts["available"]},
                    {"label": "Coupons", "value": coupon_counts["total"]},
                    {"label": "Coupons active", "value": coupon_counts["active"]},
                ],
            },
            {
                "title": "Queues",
                "stats": [
                    {"label": "Driver profiles pending", "value": driver_counts["pending"]},
                    {"label": "Driver profiles approved", "value": driver_counts["approved"]},
                    {"label": "Driver profiles rejected", "value": driver_counts["rejected"]},
                    {"label": "Driver verifications pending", "value": verification_counts["pending"]},
                ],
            },
        ]


class CustomIndexDashboard(Dashboard):
    columns = 3

    def init_with_context(self, context) -> None:
        self.children.append(StatsDashboardModule())

        self.children.append(
            modules.ModelList(
                "Orders",
                models=(
                    "orders.models.Order",
                    "orders.models.OrderItem",
                    "orders.models.OrderStatusHistory",
                    "orders.models.ManualOrder",
                    "orders.models.ShippingPackage",
                ),
            )
        )
        self.children.append(
            modules.ModelList(
                "Marketplace",
                models=(
                    "sellers.models.Restaurant",
                    "sellers.models.Category",
                    "sellers.models.Item",
                    "sellers.models.Coupon",
                    "sellers.models.CouponUsage",
                ),
            )
        )
        self.children.append(
            modules.ModelList(
                "Users",
                models=(
                    "users.models.User",
                    "users.models.CustomerProfile",
                    "users.models.DriverProfile",
                    "users.models.SellerProfile",
                    "users.models.AdminProfile",
                    "users.models.Address",
                ),
            )
        )
        self.children.append(
            modules.ModelList(
                "Drivers",
                models=(
                    "drivers.models.DriverVerification",
                    "drivers.models.DriverLocation",
                ),
            )
        )
        self.children.append(
            modules.ModelList(
                "Payments",
                models=(
                    "payments.models.PaymentMethod",
                    "payments.models.Transaction",
                ),
            )
        )
        self.children.append(modules.RecentActions("Recent Actions", 10))
