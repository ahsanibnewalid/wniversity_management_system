import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.config.settings")

import django
django.setup()

from django.db import connection

expected_engine = "django.db.backends.postgresql"
if connection.settings_dict.get("ENGINE") != expected_engine:
    print("Unexpected Django database engine:", connection.settings_dict.get("ENGINE"))
    sys.exit(1)

if connection.settings_dict.get("NAME") != "campushub":
    print("Unexpected Django database name:", connection.settings_dict.get("NAME"))
    sys.exit(1)

print("Django PostgreSQL configuration smoke test passed.")
