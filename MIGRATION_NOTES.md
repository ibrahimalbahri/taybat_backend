# Migration Notes

This refactor introduces a new roles system and profile tables and removes `User.role`.

Recommended dev flow:

```bash
python manage.py migrate
```

Notes:
- Existing users are backfilled into `Role`/`UserRole` based on the old `User.role`.
- Customer/Seller/Admin profiles are created during the backfill.
- Driver profiles are not auto-created during migration.
