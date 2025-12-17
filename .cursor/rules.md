# Cursor Rules – Taybat Backend

## Tech Stack
- Django 4.2 LTS
- Django REST Framework
- PostgreSQL (later)
- Celery + Redis (later)
- Django Channels (later)

## General Constraints
- Do NOT introduce new frameworks or libraries unless explicitly requested
- Prefer Django ORM over raw SQL
- All database writes must be transactional when applicable
- No business logic inside serializers
- No complex business logic inside views
- Use service-layer functions for domain logic

## Architecture
- Each Django app represents a business domain
- Cross-domain logic must live in a services/ directory
- Do not duplicate models across apps
- Use explicit imports (no wildcard imports)

## Coding Style
- Explicit over clever
- Readability over brevity
- No magic constants
- Add docstrings to all public functions
