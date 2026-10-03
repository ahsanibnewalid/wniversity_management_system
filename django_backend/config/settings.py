import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY=os.getenv("SECRET_KEY","django-migration-dev-key")
DEBUG=os.getenv("DEBUG","false").lower()=="true"
ALLOWED_HOSTS=[x.strip() for x in os.getenv("ALLOWED_HOSTS","*").split(",") if x.strip()]
INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.staticfiles","rest_framework","django_backend.legacy","django_backend.api"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","django.middleware.common.CommonMiddleware"]
ROOT_URLCONF="django_backend.config.urls"
TEMPLATES=[]
WSGI_APPLICATION="django_backend.config.wsgi.application"
ASGI_APPLICATION="django_backend.config.asgi.application"
DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.getenv("PGDATABASE","campushub"),"USER":os.getenv("PGUSER","campushub"),"PASSWORD":os.getenv("PGPASSWORD",""),"HOST":os.getenv("PGHOST","localhost"),"PORT":os.getenv("PGPORT","5432")}}
if os.getenv("DATABASE_URL"):
    import dj_database_url
    DATABASES["default"]=dj_database_url.parse(os.environ["DATABASE_URL"],conn_max_age=600,ssl_require=False)
LANGUAGE_CODE="en-us"; TIME_ZONE="UTC"; USE_I18N=True; USE_TZ=True
STATIC_URL="/static/"
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES":["django_backend.api.authentication.BearerTokenAuthentication"],"DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.AllowAny"],"UNAUTHENTICATED_USER":None}
