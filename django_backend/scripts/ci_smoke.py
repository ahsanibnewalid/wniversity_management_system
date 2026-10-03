import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.config.settings")

import django
django.setup()

from django.db import connection

print("Django initialized.")
print("Database engine:", connection.settings_dict.get("ENGINE"))
print("Database name:", connection.settings_dict.get("NAME"))
print("Django PostgreSQL configuration smoke test passed.")
