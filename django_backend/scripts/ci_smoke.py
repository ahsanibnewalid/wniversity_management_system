import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.config.settings")

import django
django.setup()

from django.test import Client

response = Client(HTTP_HOST="localhost").get("/healthz")
if response.status_code != 200:
    print("healthz failed:", response.status_code, response.content.decode())
    sys.exit(1)

payload = response.json()
if payload != {"status": "ok", "database": "ok"}:
    print("unexpected health response:", payload)
    sys.exit(1)

print("Django PostgreSQL integration smoke test passed.")
