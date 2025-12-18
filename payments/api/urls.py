from django.urls import path

from payments.api.admin_transaction_views import AdminTransactionListView


urlpatterns = [
    path(
        "admin/transactions/",
        AdminTransactionListView.as_view(),
        name="admin-transactions",
    ),
]