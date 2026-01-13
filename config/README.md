# Config App

Purpose
- Serve app config endpoints (version and legal URLs).

Main APIs
- `GET /api/config/version`
- `GET /api/config/legal`

Notes
- Values come from settings (`APP_LATEST_VERSION`, `APP_MIN_VERSION`, etc.).
