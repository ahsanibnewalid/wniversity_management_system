# CampusHub Django backend

The Django/DRF backend is the production target for CampusHub. It preserves the existing PostgreSQL tables through unmanaged compatibility models (`managed = False`) so the database schema is not changed by Django migrations during cutover.

## Production deployment

Render is configured to run `gunicorn django_backend.config.wsgi:application` with `/healthz` as the health check. The deployment does **not** run `manage.py migrate`.

Required production environment values:
- `DATABASE_URL`: existing PostgreSQL database.
- `SECRET_KEY`: generated/secret value.
- `DEBUG=false`.
- `ALLOWED_HOSTS`: Render hostname plus any custom API hostname.
- `CORS_ALLOWED_ORIGINS`: comma-separated trusted web origins.
- SMTP settings (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`) for verification/password-reset mail.

## Safe cutover

1. Take a PostgreSQL backup/snapshot.
2. Deploy the Django service against a staging copy of the existing database first.
3. Run `python manage.py check --deploy`.
4. Run `scripts/smoke.sh` against staging.
5. Confirm login, profile, academic, community, messaging, event, campus-service and PDF flows with real staging data.
6. Point the production API service at Django.
7. Monitor application and database logs.
8. Roll back the service to the Flask process if a production-only regression appears.

**Do not run `python manage.py migrate` against the legacy production database during this compatibility phase.**

## Security

Production settings require a real `SECRET_KEY` and `ALLOWED_HOSTS`, enable HTTPS/security headers and secure cookies, require TLS for `DATABASE_URL` by default, and restrict CORS to explicitly configured origins.

Verification and password-reset tokens are emailed in production and are only returned in API responses when `DEBUG=true` for local development/testing.

## Local run

```bash
cd django_backend
pip install -r requirements.txt
export DATABASE_URL='postgresql://...'
export SECRET_KEY='local-development-secret'
export DEBUG=true
export ALLOWED_HOSTS='localhost,127.0.0.1'
python manage.py check
python manage.py runserver
```
