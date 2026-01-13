# Orders App

Purpose
- Unified order model for food, shipping, taxi.
- Customer checkout flows and order history.
- Admin order dashboard and exports.

Key Models
- Order, OrderItem, ShippingPackage
- OrderDriverSuggestion, OrderStatusHistory, ManualOrder
- Export (admin reports)

Main APIs
- Customer checkout: `/api/customer/checkout/*`
- Customer orders: `/api/customer/orders/*`
- Admin orders: `/api/admin/orders/*` and export endpoints
- Seller manual orders: `/api/seller/orders/manual/`
- Seller exports: `/api/seller/orders/export/*`

Notes
- Pricing logic in `orders/services/pricing.py`.
- Driver eligibility rules in `orders/services/eligibility.py`.
