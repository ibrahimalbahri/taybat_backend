from django.urls import path
from orders.api.customer_views import (
    CustomerFoodCheckoutView,
    CustomerOrderListView,
    CustomerOrderDetailView,
)

urlpatterns = [
    path("customer/checkout/food/", CustomerFoodCheckoutView.as_view(), name="customer-food-checkout"),
    path("customer/orders/", CustomerOrderListView.as_view(), name="customer-orders"),
    path("customer/orders/<int:pk>/", CustomerOrderDetailView.as_view(), name="customer-order-detail"),
]
