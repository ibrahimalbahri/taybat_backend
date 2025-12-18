from django.urls import path

from restaurants.api.customer_views import (
    CustomerRestaurantListView,
    CustomerRestaurantDetailView,
    CustomerItemSearchView,
)
from restaurants.api.seller_views import (
    SellerOrderListView,
    SellerOrderDetailView,
    SellerOrderAcceptView,
    SellerOrderStatusUpdateView,
    SellerCategoryListCreateView,
    SellerCategoryDetailView,
    SellerItemListCreateView,
    SellerItemDetailView,
    SellerItemStatsView,
)


urlpatterns = [
    # Customer-facing endpoints
    path(
        "customer/restaurants/",
        CustomerRestaurantListView.as_view(),
        name="customer-restaurants",
    ),
    path(
        "customer/restaurants/<int:pk>/",
        CustomerRestaurantDetailView.as_view(),
        name="customer-restaurant-detail",
    ),
    path(
        "customer/items/search/",
        CustomerItemSearchView.as_view(),
        name="customer-item-search",
    ),
    # Seller-facing endpoints
    path(
        "seller/orders/",
        SellerOrderListView.as_view(),
        name="seller-orders",
    ),
    path(
        "seller/orders/<int:pk>/",
        SellerOrderDetailView.as_view(),
        name="seller-order-detail",
    ),
    path(
        "seller/orders/<int:pk>/accept/",
        SellerOrderAcceptView.as_view(),
        name="seller-order-accept",
    ),
    path(
        "seller/orders/<int:pk>/status/",
        SellerOrderStatusUpdateView.as_view(),
        name="seller-order-status-update",
    ),
    path(
        "seller/categories/",
        SellerCategoryListCreateView.as_view(),
        name="seller-categories",
    ),
    path(
        "seller/categories/<int:pk>/",
        SellerCategoryDetailView.as_view(),
        name="seller-category-detail",
    ),
    path(
        "seller/items/",
        SellerItemListCreateView.as_view(),
        name="seller-items",
    ),
    path(
        "seller/items/<int:pk>/",
        SellerItemDetailView.as_view(),
        name="seller-item-detail",
    ),
    path(
        "seller/items/<int:pk>/stats/",
        SellerItemStatsView.as_view(),
        name="seller-item-stats",
    ),
]
