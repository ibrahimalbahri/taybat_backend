from __future__ import annotations

from admin_tools.dashboard import Dashboard, modules
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone


class StatsDashboardModule(modules.DashboardModule):
    title = "Platform Stats"
    template = "admin_tools/dashboard/modules/taybat_stats.html"

    def init_with_context(self, context) -> None:
        request = context.get("request")
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

        params = request.GET if request else {}
        date_preset = params.get("date_range", "7d")
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        order_type_filter = params.get("order_type")
        order_status_filter = params.get("order_status")
        restaurant_filter = params.get("restaurant")
        payment_status_filter = params.get("payment_status")
        payment_type_filter = params.get("payment_type")

        def parse_date(value: str | None):
            if not value:
                return None
            try:
                return timezone.datetime.fromisoformat(value).replace(tzinfo=timezone.get_current_timezone())
            except ValueError:
                return None

        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        if date_preset == "today":
            start_dt = start_today
            end_dt = None
        elif date_preset == "30d":
            start_dt = now - timezone.timedelta(days=30)
            end_dt = None
        elif date_preset == "custom":
            start_dt = start_dt
            end_dt = end_dt
        else:
            start_dt = now - timezone.timedelta(days=7)
            end_dt = None

        order_qs = Order.objects.all()
        if start_dt:
            order_qs = order_qs.filter(created_at__gte=start_dt)
        if end_dt:
            order_qs = order_qs.filter(created_at__lte=end_dt)
        if order_type_filter:
            order_qs = order_qs.filter(order_type=order_type_filter)
        if order_status_filter:
            order_qs = order_qs.filter(status=order_status_filter)
        if restaurant_filter:
            order_qs = order_qs.filter(restaurant_id=restaurant_filter)

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
        if start_dt:
            txn_qs = txn_qs.filter(created_at__gte=start_dt)
        if end_dt:
            txn_qs = txn_qs.filter(created_at__lte=end_dt)
        if payment_status_filter:
            txn_qs = txn_qs.filter(status=payment_status_filter)
        if payment_type_filter:
            txn_qs = txn_qs.filter(type=payment_type_filter)
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

        def build_chart(rows: list[dict]) -> dict:
            max_value = max((row["value"] for row in rows), default=0) or 1
            for row in rows:
                row["percent"] = round((row["value"] / max_value) * 100, 2)
            return {"rows": rows, "max": max_value}

        order_status_chart = build_chart(
            [
                {"label": "Pending", "value": order_counts["pending"]},
                {"label": "Searching", "value": order_counts["searching"]},
                {"label": "On the way", "value": order_counts["on_the_way"]},
                {"label": "Completed", "value": order_counts["completed"]},
                {"label": "Cancelled", "value": order_counts["cancelled"]},
            ]
        )
        order_type_chart = build_chart(
            [
                {"label": "Food", "value": order_type_counts["food"]},
                {"label": "Shipping", "value": order_type_counts["shipping"]},
                {"label": "Taxi", "value": order_type_counts["taxi"]},
            ]
        )
        payment_status_chart = build_chart(
            [
                {"label": "Succeeded", "value": txn_counts["succeeded"]},
                {"label": "Pending", "value": txn_counts["pending"]},
                {"label": "Failed", "value": txn_counts["failed"]},
                {"label": "Cancelled", "value": txn_counts["cancelled"]},
            ]
        )

        self.filters = {
            "date_range": date_preset,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "order_type": order_type_filter or "",
            "order_status": order_status_filter or "",
            "restaurant": restaurant_filter or "",
            "payment_status": payment_status_filter or "",
            "payment_type": payment_type_filter or "",
        }
        self.filter_options = {
            "order_types": OrderType.choices,
            "order_statuses": OrderStatus.choices,
            "payment_statuses": TransactionStatus.choices,
            "payment_types": TransactionType.choices,
            "restaurants": Restaurant.objects.only("id", "name").order_by("name"),
        }
        self.charts = {
            "order_status": order_status_chart,
            "order_type": order_type_chart,
            "payment_status": payment_status_chart,
        }

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
