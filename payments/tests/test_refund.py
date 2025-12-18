import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from payments.models import Transaction, TransactionType, TransactionStatus, PaymentMethod

@pytest.mark.django_db
def test_admin_refund_creates_refund_tx(admin_user, customer_user, order_factory):
    order = order_factory(customer=customer_user, total_amount=Decimal("10.00"), tip=Decimal("0.00"))
    # seed successful payment tx
    Transaction.objects.create(
        user=customer_user, order=order, provider="MOCK", provider_ref="mock_charge_1",
        type=TransactionType.PAYMENT, status=TransactionStatus.SUCCEEDED, amount=Decimal("10.00"), currency="EUR"
    )

    c = APIClient()
    c.force_authenticate(admin_user)

    url = f"/api/admin/orders/{order.id}/refund/"
    r = c.post(url, {"amount": "5.00", "reason": "test"}, format="json")
    # assert r.status_code == 200
    assert Transaction.objects.filter(order=order, type=TransactionType.REFUND).exists()
