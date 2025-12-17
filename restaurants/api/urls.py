from django.urls import path
from restaurants.api.customer_views import (
    CustomerRestaurantListView,
    CustomerRestaurantDetailView,
    CustomerItemSearchView,
)

urlpatterns = [
    path("customer/restaurants/", CustomerRestaurantListView.as_view(), name="customer-restaurants"),
    path("customer/restaurants/<int:pk>/", CustomerRestaurantDetailView.as_view(), name="customer-restaurant-detail"),
    path("customer/items/search/", CustomerItemSearchView.as_view(), name="customer-item-search"),
]
