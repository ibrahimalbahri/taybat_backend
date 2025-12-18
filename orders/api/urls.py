from django.urls import path

from orders.api.customer_views import (
    CustomerFoodCheckoutView,
    CustomerOrderListView,
    CustomerOrderDetailView,
)
from orders.api.customer_pricing_views import (
    TaxiPricePreviewView,
    ShippingPricePreviewView,
)
from orders.api.customer_service_checkout_views import (
    TaxiCheckoutView,
    ShippingCheckoutView,
)
from orders.api.seller_manual_order_views import SellerManualOrderCreateView


urlpatterns = [
    # Customer-facing endpoints
    path(
        "customer/checkout/food/",
        CustomerFoodCheckoutView.as_view(),
        name="customer-food-checkout",
    ),
    path(
        "customer/checkout/taxi/",
        TaxiCheckoutView.as_view(),
        name="customer-taxi-checkout",
    ),
    path(
        "customer/checkout/shipping/",
        ShippingCheckoutView.as_view(),
        name="customer-shipping-checkout",
    ),
    path("customer/orders/", CustomerOrderListView.as_view(), name="customer-orders"),
    path(
        "customer/orders/<int:pk>/",
        CustomerOrderDetailView.as_view(),
        name="customer-order-detail",
    ),
    path(
        "customer/preview/taxi/",
        TaxiPricePreviewView.as_view(),
        name="customer-taxi-preview",
    ),
    path(
        "customer/preview/shipping/",
        ShippingPricePreviewView.as_view(),
        name="customer-shipping-preview",
    ),
    # Seller-facing endpoints
    path(
        "seller/orders/manual/",
        SellerManualOrderCreateView.as_view(),
        name="seller-manual-order-create",
    ),
]
