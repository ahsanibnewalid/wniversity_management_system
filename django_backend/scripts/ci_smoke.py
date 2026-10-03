import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.config.settings")

import django
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
except Exception as exc:
    print("Django PostgreSQL connection failed:", repr(exc))
    sys.exit(1)

if result != (1,):
    print("Unexpected PostgreSQL result:", result)
    sys.exit(1)

print("Django PostgreSQL integration smoke test passed.")
