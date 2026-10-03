# CampusHub Django backend

The Django/DRF migration implementation is complete on the `django-migration` branch.

It preserves the existing PostgreSQL schema and exposes the CampusHub API under `/api/v1/` while the Flask implementation remains available on `main`.

## Safety model

The compatibility ORM uses the existing table names and `managed = False`. Django therefore does not own or mutate the existing schema during this migration phase.

Production cutover requires:
1. PostgreSQL backup.
2. A staging copy of the existing database.
3. `DATABASE_URL` configured for the Django service.
4. `python manage.py check`.
5. API smoke/contract tests against staging.
6. Switch the API process to Django.
7. Monitor logs and rollback to Flask if a production-only issue appears.

Do not run `python manage.py migrate` against the legacy production schema during the compatibility phase.

## Run locally

```bash
cd django_backend
pip install -r requirements.txt
export DATABASE_URL='postgresql://...'
python manage.py check
python manage.py runserver
```

The existing web and mobile clients can continue using `/api/v1/` without changing their base API contract.