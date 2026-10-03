# CampusHub Django migration

This branch adds a compatibility-first Django/DRF backend beside the existing Flask backend.

## Database safety

The `legacy` models use the existing PostgreSQL table names and `managed = False`. Django will not create, alter, or delete those CampusHub tables.

Before production cutover:
1. Back up PostgreSQL.
2. Point `DATABASE_URL` at the existing database.
3. Run `python manage.py check`.
4. Run compatibility tests.
5. Migrate endpoint-by-endpoint.
6. Only after cutover should Django migrations own schema changes.

Existing integer IDs and table names are preserved.

## Current migrated API slice

- `/healthz`
- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/auth/logout`
- `/api/v1/auth/logout-all`
- `/api/v1/institutions`
- `/api/v1/my/institutions`
- `/api/v1/institutions/<id>/join`
- `/api/v1/profile`

The existing Flask application remains untouched on `main` while the Django API is migrated incrementally.

## Run

```bash
cd django_backend
pip install -r requirements.txt
export DATABASE_URL='postgresql://...'
python manage.py check
python manage.py runserver
```

Do not run schema migrations against the legacy tables during this compatibility phase.
