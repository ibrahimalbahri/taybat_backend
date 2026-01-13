# Payments App

Purpose
- Payment methods, transactions, and refunds.
- Admin reconciliation and transaction audit.

Key Models
- PaymentMethod, Transaction

Main APIs
- Customer payment methods: `/api/payments/`, `/api/payments/<id>/`
- Admin transactions: `/api/payments/admin/transactions/`
- Admin refunds: `/api/orders/<id>/refund/`
- Seller refunds: `/api/seller/orders/<id>/refund/`
- Admin reconciliation: `/api/reconciliation/orders/`

Notes
- Refund/capture logic in `payments/services/*`.
