from django.urls import path

from payments.api.admin_reconciliation_views import AdminReconciliationOrdersView
from payments.api.admin_refund_views import AdminOrderRefundView
from payments.api.admin_transaction_views import AdminTransactionListView
from payments.api.customer_payment_method_views import PaymentMethodListCreateView, PaymentMethodUpdateDeleteView


urlpatterns = [
    path(
        "payments/admin/transactions/",
        AdminTransactionListView.as_view(),
        name="payments-admin-transactions",
    ),
    path("reconciliation/orders/", AdminReconciliationOrdersView.as_view(), 
        name="admin-reconciliation-orders"
    ),
    path("payments/", PaymentMethodListCreateView.as_view(), name="customer-payment-methods"),
    path("payments/<int:pk>/", PaymentMethodUpdateDeleteView.as_view(), name="customer-payment-method-detail"),
    path("orders/<int:order_id>/refund/", AdminOrderRefundView.as_view(), name="admin-order-refund"),
]