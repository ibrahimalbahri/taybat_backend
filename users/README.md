# Users App

Purpose
- Core identity models and role system (multi-role users).
- Profiles: customer, seller, admin, driver.
- OTP auth helpers and user-facing profile updates.

Key Models
- User, Role, UserRole
- CustomerProfile, SellerProfile, AdminProfile, DriverProfile
- Address

Main APIs
- Auth: `POST /api/auth/otp/request`, `POST /api/auth/otp/verify`
- Me: `GET /api/me/`, `PATCH /api/me/`
- Profiles: `PATCH /api/customer/profile/`, `PATCH /api/seller/profile/`, `PATCH /api/driver/profile/`
- Addresses: `GET/POST /api/addresses/`, `GET/PATCH/PUT/DELETE /api/addresses/<id>/`

Notes
- Role checks use `User.has_role(...)` and permission classes in `users/permissions.py`.
- Driver profiles and statuses are here (not in drivers app).
