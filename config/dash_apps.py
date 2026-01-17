from __future__ import annotations

from datetime import date, timedelta

from dash import Input, Output, dcc, html
from django.db.models import (
    Count,
    DecimalField,
    DurationField,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from django_plotly_dash import DjangoDash

from orders.models import Order, OrderStatus, OrderStatusHistory, OrderType
from payments.models import Transaction, TransactionStatus, TransactionType


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


app = DjangoDash("TaybatDash")
app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Date range"),
                        dcc.Dropdown(
                            id="dash-date-range",
                            options=[
                                {"label": "Today", "value": "today"},
                                {"label": "Last 7 days", "value": "7d"},
                                {"label": "Last 30 days", "value": "30d"},
                                {"label": "Custom", "value": "custom"},
                            ],
                            value="7d",
                            clearable=False,
                        ),
                    ],
                    className="dash-filter",
                ),
                html.Div(
                    [
                        html.Label("Custom range  "),
                        dcc.DatePickerRange(
                            id="dash-date-picker",
                            display_format="YYYY-MM-DD",
                        ),
                    ],
                    className="dash-filter",
                ),
                html.Div(
                    [
                        html.Label("Order type"),
                        dcc.Dropdown(
                            id="dash-order-type",
                            options=[{"label": label, "value": value} for value, label in [('All', 'All')] + OrderType.choices],
                            placeholder="All",
                            clearable=True,
                        ),
                    ],
                    className="dash-filter",
                ),
                html.Div(
                    [
                        html.Label("Order status"),
                        dcc.Dropdown(
                            id="dash-order-status",
                            options=[{"label": label, "value": value} for value, label in [('All', 'All')] + OrderStatus.choices],
                            placeholder="All",
                            clearable=True,
                        ),
                    ],
                    className="dash-filter",
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "12px",
                "marginBottom": "18px",
                "padding": "14px",
                "maxWidth": "420px",
                "backgroundColor": "#f5f7ff",
                "border": "1px solid #dfe6f3",
                "borderRadius": "12px",
                "boxShadow": "0 8px 18px rgba(29, 42, 74, 0.08)",
            },
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="dash-order-status-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #2b7cff",
                    },
                ),
                html.Div(
                    dcc.Graph(id="dash-order-type-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #e67e22",
                    },
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(340px, 1fr))",
                "gap": "18px",
                "marginBottom": "18px",
            },
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="dash-revenue-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #27ae60",
                    },
                ),
                html.Div(
                    dcc.Graph(id="dash-payment-status-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #6c5ce7",
                    },
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(340px, 1fr))",
                "gap": "18px",
                "marginBottom": "18px",
            },
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="dash-revenue-type-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #00b894",
                    },
                ),
                html.Div(
                    dcc.Graph(id="dash-top-restaurants-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #fdcb6e",
                    },
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(340px, 1fr))",
                "gap": "18px",
                "marginBottom": "18px",
            },
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="dash-completion-rate-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #0984e3",
                    },
                ),
                html.Div(
                    dcc.Graph(id="dash-cancellations-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #d63031",
                    },
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(340px, 1fr))",
                "gap": "18px",
                "marginBottom": "18px",
            },
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="dash-supply-demand-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #2ecc71",
                    },
                ),
                html.Div(
                    dcc.Graph(id="dash-fulfillment-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #8e44ad",
                    },
                ),
                html.Div(
                    dcc.Graph(id="dash-payment-success-rate-chart"),
                    style={
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e0e6f0",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "boxShadow": "0 10px 20px rgba(29, 42, 74, 0.12)",
                        "borderTop": "3px solid #f39c12",
                    },
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(340px, 1fr))",
                "gap": "18px",
                "marginBottom": "18px",
            },
        ),
    ],
    style={"padding": "18px", "maxWidth": "1280px", "margin": "0 auto"},
)


@app.callback(
    Output("dash-order-status-chart", "figure"),
    Output("dash-order-type-chart", "figure"),
    Output("dash-revenue-chart", "figure"),
    Output("dash-payment-status-chart", "figure"),
    Output("dash-revenue-type-chart", "figure"),
    Output("dash-top-restaurants-chart", "figure"),
    Output("dash-completion-rate-chart", "figure"),
    Output("dash-cancellations-chart", "figure"),
    Output("dash-supply-demand-chart", "figure"),
    Output("dash-fulfillment-chart", "figure"),
    Output("dash-payment-success-rate-chart", "figure"),
    Input("dash-date-range", "value"),
    Input("dash-date-picker", "start_date"),
    Input("dash-date-picker", "end_date"),
    Input("dash-order-type", "value"),
    Input("dash-order-status", "value"),
)
def update_charts(date_range, start_date, end_date, order_type, order_status):
    now = timezone.localdate()
    start_dt = None
    end_dt = None

    if date_range == "today":
        start_dt = now
    elif date_range == "30d":
        start_dt = now - timedelta(days=30)
    elif date_range == "custom":
        start_dt = _parse_date(start_date)
        end_dt = _parse_date(end_date)
    else:
        start_dt = now - timedelta(days=7)

    order_qs = Order.objects.all()
    if start_dt:
        order_qs = order_qs.filter(created_at__date__gte=start_dt)
    if end_dt:
        order_qs = order_qs.filter(created_at__date__lte=end_dt)
    if order_type and order_type != "All":
        order_qs = order_qs.filter(order_type=order_type)
    if order_status and order_status != "All":
        order_qs = order_qs.filter(status=order_status)

    status_counts = order_qs.aggregate(
        pending=Count("id", filter=Q(status=OrderStatus.PENDING)),
        searching=Count("id", filter=Q(status=OrderStatus.SEARCHING_FOR_DRIVER)),
        on_the_way=Count("id", filter=Q(status=OrderStatus.ON_THE_WAY)),
        completed=Count("id", filter=Q(status=OrderStatus.COMPLETED)),
        cancelled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
    )
    status_chart = {
        "data": [
            {
                "x": ["Pending", "Searching", "On the way", "Completed", "Cancelled"],
                "y": [
                    status_counts["pending"],
                    status_counts["searching"],
                    status_counts["on_the_way"],
                    status_counts["completed"],
                    status_counts["cancelled"],
                ],
                "type": "bar",
                "marker": {"color": "#2b7cff"},
            }
        ],
        "layout": {"title": "Orders by status", "height": 320, "margin": {"t": 40, "l": 40, "r": 20, "b": 40}},
    }

    type_counts = order_qs.aggregate(
        food=Count("id", filter=Q(order_type=OrderType.FOOD)),
        shipping=Count("id", filter=Q(order_type=OrderType.SHIPPING)),
        taxi=Count("id", filter=Q(order_type=OrderType.TAXI)),
    )
    type_chart = {
        "data": [
            {
                "labels": ["Food", "Shipping", "Taxi"],
                "values": [type_counts["food"], type_counts["shipping"], type_counts["taxi"]],
                "type": "pie",
                "hole": 0.45,
            }
        ],
        "layout": {"title": "Orders by type", "height": 320, "margin": {"t": 40, "l": 20, "r": 20, "b": 40}},
    }

    txn_qs = Transaction.objects.filter(
        status=TransactionStatus.SUCCEEDED,
        type__in=[TransactionType.PAYMENT, TransactionType.TIP, TransactionType.ADJUSTMENT],
    )
    if start_dt:
        txn_qs = txn_qs.filter(created_at__date__gte=start_dt)
    if end_dt:
        txn_qs = txn_qs.filter(created_at__date__lte=end_dt)

    revenue_by_day = {
        row["day"]: row["total"]
        for row in txn_qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))
    }
    if start_dt and end_dt:
        series_start = start_dt
        series_end = end_dt
    else:
        series_end = now
        series_start = start_dt or (now - timedelta(days=7))

    dates = []
    totals = []
    cursor = series_start
    while cursor <= series_end:
        dates.append(cursor.isoformat())
        totals.append(float(revenue_by_day.get(cursor, 0)))
        cursor += timedelta(days=1)

    revenue_chart = {
        "data": [{"x": dates, "y": totals, "type": "scatter", "mode": "lines+markers"}],
        "layout": {"title": "Revenue by day", "height": 320, "margin": {"t": 40, "l": 40, "r": 20, "b": 40}},
    }

    txn_status_qs = Transaction.objects.all()
    if start_dt:
        txn_status_qs = txn_status_qs.filter(created_at__date__gte=start_dt)
    if end_dt:
        txn_status_qs = txn_status_qs.filter(created_at__date__lte=end_dt)

    payment_status_counts = txn_status_qs.aggregate(
        pending=Count("id", filter=Q(status=TransactionStatus.PENDING)),
        succeeded=Count("id", filter=Q(status=TransactionStatus.SUCCEEDED)),
        failed=Count("id", filter=Q(status=TransactionStatus.FAILED)),
        cancelled=Count("id", filter=Q(status=TransactionStatus.CANCELLED)),
    )
    payment_status_chart = {
        "data": [
            {
                "x": ["Succeeded", "Pending", "Failed", "Cancelled"],
                "y": [
                    payment_status_counts["succeeded"],
                    payment_status_counts["pending"],
                    payment_status_counts["failed"],
                    payment_status_counts["cancelled"],
                ],
                "type": "bar",
                "marker": {"color": "#f57c00"},
            }
        ],
        "layout": {"title": "Payments by status", "height": 320, "margin": {"t": 40, "l": 40, "r": 20, "b": 40}},
    }

    revenue_type_qs = Transaction.objects.filter(
        status=TransactionStatus.SUCCEEDED,
        type__in=[TransactionType.PAYMENT, TransactionType.TIP, TransactionType.ADJUSTMENT],
        order__isnull=False,
    )
    if start_dt:
        revenue_type_qs = revenue_type_qs.filter(created_at__date__gte=start_dt)
    if end_dt:
        revenue_type_qs = revenue_type_qs.filter(created_at__date__lte=end_dt)
    revenue_type_qs = revenue_type_qs.select_related("order")

    type_totals = {
        OrderType.FOOD: [],
        OrderType.SHIPPING: [],
        OrderType.TAXI: [],
    }
    type_dates = []
    revenue_rows = (
        revenue_type_qs.annotate(day=TruncDate("created_at"))
        .values("day", "order__order_type")
        .annotate(total=Coalesce(Sum("amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))
    )
    revenue_by_day = {}
    for row in revenue_rows:
        revenue_by_day.setdefault(row["day"], {})[row["order__order_type"]] = float(row["total"])

    cursor = series_start
    while cursor <= series_end:
        type_dates.append(cursor.isoformat())
        day_values = revenue_by_day.get(cursor, {})
        for order_type_key in type_totals:
            type_totals[order_type_key].append(day_values.get(order_type_key, 0))
        cursor += timedelta(days=1)

    revenue_type_chart = {
        "data": [
            {"x": type_dates, "y": type_totals[OrderType.FOOD], "type": "bar", "name": "Food"},
            {"x": type_dates, "y": type_totals[OrderType.SHIPPING], "type": "bar", "name": "Shipping"},
            {"x": type_dates, "y": type_totals[OrderType.TAXI], "type": "bar", "name": "Taxi"},
        ],
        "layout": {
            "title": "Revenue by order type",
            "barmode": "stack",
            "height": 320,
            "margin": {"t": 40, "l": 40, "r": 20, "b": 40},
        },
    }

    top_restaurants = (
        order_qs.filter(restaurant__isnull=False)
        .values("restaurant__name")
        .annotate(
            orders=Count("id"),
            revenue=Coalesce(Sum("total_amount"), 0, output_field=DecimalField(max_digits=10, decimal_places=2)),
        )
        .order_by("-orders")[:10]
    )
    restaurant_names = [row["restaurant__name"] for row in top_restaurants]
    restaurant_orders = [row["orders"] for row in top_restaurants]
    restaurant_revenue = [float(row["revenue"]) for row in top_restaurants]
    top_restaurants_chart = {
        "data": [
            {"x": restaurant_orders, "y": restaurant_names, "type": "bar", "orientation": "h", "name": "Orders"},
            {
                "x": restaurant_revenue,
                "y": restaurant_names,
                "type": "bar",
                "orientation": "h",
                "name": "Revenue",
                "xaxis": "x2",
            },
        ],
        "layout": {
            "title": "Top restaurants",
            "height": 320,
            "margin": {"t": 40, "l": 120, "r": 20, "b": 40},
            "xaxis": {"title": "Orders"},
            "xaxis2": {"title": "Revenue", "overlaying": "x", "side": "top"},
        },
    }

    completion_rows = (
        order_qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=OrderStatus.COMPLETED)),
            cancelled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
        )
        .order_by("day")
    )
    completion_dates = [row["day"].isoformat() for row in completion_rows]
    completion_rate = [
        (row["completed"] / row["total"] * 100) if row["total"] else 0 for row in completion_rows
    ]
    cancellations = [row["cancelled"] for row in completion_rows]

    completion_rate_chart = {
        "data": [{"x": completion_dates, "y": completion_rate, "type": "scatter", "mode": "lines+markers"}],
        "layout": {"title": "Completion rate (%)", "height": 320, "margin": {"t": 40, "l": 40, "r": 20, "b": 40}},
    }
    cancellations_chart = {
        "data": [{"x": completion_dates, "y": cancellations, "type": "bar", "marker": {"color": "#e53935"}}],
        "layout": {"title": "Cancellations by day", "height": 320, "margin": {"t": 40, "l": 40, "r": 20, "b": 40}},
    }

    from users.models import DriverProfile

    online_drivers = DriverProfile.objects.filter(is_online=True).count()
    searching_orders = order_qs.filter(
        status__in=[OrderStatus.SEARCHING_FOR_DRIVER, OrderStatus.DRIVER_NOTIFICATION_SENT]
    ).count()
    supply_demand_chart = {
        "data": [
            {
                "x": ["Online drivers", "Searching orders"],
                "y": [online_drivers, searching_orders],
                "type": "bar",
                "marker": {"color": ["#2e7d32", "#c62828"]},
            }
        ],
        "layout": {"title": "Supply vs demand (current)", "height": 320, "margin": {"t": 40, "l": 40, "r": 20, "b": 40}},
    }

    completed_ts = OrderStatusHistory.objects.filter(
        order_id=OuterRef("pk"),
        status=OrderStatus.COMPLETED,
    ).order_by("timestamp").values("timestamp")[:1]
    fulfillment_qs = (
        order_qs.annotate(completed_at=Subquery(completed_ts))
        .exclude(completed_at__isnull=True)
        .annotate(
            fulfillment=ExpressionWrapper(F("completed_at") - F("created_at"), output_field=DurationField())
        )
    )
    fulfillment_durations = []
    for duration in fulfillment_qs.values_list("fulfillment", flat=True):
        if duration:
            fulfillment_durations.append(duration.total_seconds() / 60)

    fulfillment_durations.sort()
    if fulfillment_durations:
        avg_minutes = sum(fulfillment_durations) / len(fulfillment_durations)
        p50 = fulfillment_durations[int((len(fulfillment_durations) - 1) * 0.5)]
        p90 = fulfillment_durations[int((len(fulfillment_durations) - 1) * 0.9)]
    else:
        avg_minutes = p50 = p90 = 0

    fulfillment_chart = {
        "data": [
            {
                "x": ["Avg", "P50", "P90"],
                "y": [avg_minutes, p50, p90],
                "type": "bar",
                "marker": {"color": "#6a1b9a"},
            }
        ],
        "layout": {
            "title": "Fulfillment time (minutes)",
            "height": 320,
            "margin": {"t": 40, "l": 40, "r": 20, "b": 40},
        },
    }

    txn_rate_rows = (
        txn_status_qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            total=Count("id"),
            succeeded=Count("id", filter=Q(status=TransactionStatus.SUCCEEDED)),
        )
        .order_by("day")
    )
    rate_dates = [row["day"].isoformat() for row in txn_rate_rows]
    success_rates = [(row["succeeded"] / row["total"] * 100) if row["total"] else 0 for row in txn_rate_rows]
    payment_success_rate_chart = {
        "data": [{"x": rate_dates, "y": success_rates, "type": "scatter", "mode": "lines+markers"}],
        "layout": {
            "title": "Payment success rate (%)",
            "height": 320,
            "margin": {"t": 40, "l": 40, "r": 20, "b": 40},
        },
    }

    return (
        status_chart,
        type_chart,
        revenue_chart,
        payment_status_chart,
        revenue_type_chart,
        top_restaurants_chart,
        completion_rate_chart,
        cancellations_chart,
        supply_demand_chart,
        fulfillment_chart,
        payment_success_rate_chart,
    )
