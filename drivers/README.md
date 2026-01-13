# Drivers App

Purpose
- Driver-facing order workflow (suggestions, accept/reject, status updates).
- Admin driver verification workflow.

Key Models
- DriverVerification (DriverProfile is in users app).

Main APIs
- Driver actions: `/api/drivers/*` (toggle online, suggested orders, accept/reject, update status).
- Admin verification: `/api/admin/drivers/verification-queue/`, `/api/admin/drivers/<id>/verify/`, `/api/admin/drivers/<id>/verification-history/`

Notes
- Driver eligibility uses `orders/services/eligibility.py`.
- Approved driver gating via `IsApprovedDriver`.
