# Django migration status

Branch: `django-migration`

## Implementation status: COMPLETE

The Django/DRF compatibility backend is implemented alongside the existing Flask backend.

### Included
- PostgreSQL compatibility models for the existing tables, using `managed = False`.
- Existing integer IDs/table names preserved.
- Existing bearer-token authentication.
- Existing Werkzeug password hashes.
- Authentication, verification and password recovery.
- Institutions, memberships, departments, sessions, years and administration.
- Faculties, programs, courses, offerings, enrollment, attendance, assignments, submissions, grading, exams, results, transcripts and timetables.
- Community groups, membership, posts, comments, reactions, attachments, polls and votes.
- Messages, profiles, search and dashboard.
- Events, registrations, tickets, check-in, certificates and clubs.
- Documents, service requests, fees, campus services, lost/found, emergency contacts, buses, hostel, library and cafeteria.
- Notifications, announcements and push devices.
- Student ID and transcript PDF endpoints.
- `/api/v1` route compatibility layer.
- CI validation for Python compilation and Django system checks.

### Database safety
No Django migration has been run against the existing PostgreSQL schema. Legacy models are unmanaged so this branch cannot accidentally create, alter or delete the existing CampusHub tables through Django migrations.

### Validation
The latest GitHub Actions run for this branch completed successfully:
- Python compilation: PASS
- Django `manage.py check`: PASS

### Production cutover
The code migration is complete. Production cutover is intentionally a separate deployment operation because it requires the real PostgreSQL `DATABASE_URL`, a verified database backup, staging smoke tests against a copy of the production database, and then switching the API process from Flask to Django.

Do not run `python manage.py migrate` against the legacy database yet.