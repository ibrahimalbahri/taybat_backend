from django.urls import path

from sellers.api.customer_views import (
    CustomerRestaurantListView,
    CustomerRestaurantDetailView,
    CustomerItemSearchView,
)
from sellers.api.seller_views import (
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
from sellers.api.seller_coupon_views import (
    SellerCouponCreateView,
    SellerCouponUpdateView,
)
from sellers.api.admin_restaurant_views import (
    AdminRestaurantActivateView,
    AdminRestaurantDeactivateView,
)
from sellers.api.admin_coupon_views import (
    AdminCouponListView,
    AdminCouponDetailView,
    AdminCouponDisableView,
    AdminCouponEnableView,
    AdminCouponUsageView,
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
    path(
        "seller/coupons/",
        SellerCouponCreateView.as_view(),
        name="seller-coupon-create",
    ),
    path(
        "seller/coupons/<int:pk>/",
        SellerCouponUpdateView.as_view(),
        name="seller-coupon-update",
    ),
    # Admin restaurant controls
    path(
        "admin/restaurants/<int:pk>/activate/",
        AdminRestaurantActivateView.as_view(),
        name="admin-restaurant-activate",
    ),
    path(
        "admin/restaurants/<int:pk>/deactivate/",
        AdminRestaurantDeactivateView.as_view(),
        name="admin-restaurant-deactivate",
    ),
    # Admin coupon oversight + audit
    path(
        "admin/coupons/",
        AdminCouponListView.as_view(),
        name="admin-coupons",
    ),
    path(
        "admin/coupons/<int:pk>/",
        AdminCouponDetailView.as_view(),
        name="admin-coupon-detail",
    ),
    path(
        "admin/coupons/<int:pk>/disable/",
        AdminCouponDisableView.as_view(),
        name="admin-coupon-disable",
    ),
    path(
        "admin/coupons/<int:pk>/enable/",
        AdminCouponEnableView.as_view(),
        name="admin-coupon-enable",
    ),
    path(
        "admin/coupons/<int:pk>/usage/",
        AdminCouponUsageView.as_view(),
        name="admin-coupon-usage",
    ),
]
