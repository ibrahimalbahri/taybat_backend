# Sellers App

Purpose
- Restaurant/catalog management (restaurants, categories, items).
- Coupons for restaurants, and admin oversight.

Key Models
- Restaurant, Category, Item
- Coupon, CouponUsage

Main APIs
- Customer restaurant views: `/api/customer/restaurants/*`, `/api/customer/items/search/`
- Seller ops: `/api/seller/*` (orders, categories, items, coupons, restaurants CRUD)
- Admin controls: `/api/admin/restaurants/*`, `/api/admin/coupons/*`

Notes
- Seller ownership enforced via `restaurant.owner_user`.
