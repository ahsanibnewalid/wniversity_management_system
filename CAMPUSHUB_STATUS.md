# CampusHub

CampusHub is a university management and campus community platform with a Flask API, responsive web client, and Expo/React Native mobile client.

## Implemented platform areas

- Authentication, bearer sessions, logout-all, password reset flow, profile setup and verification state
- University → faculty → department → program → session → academic year → semester → course hierarchy
- Institution memberships, join requests, role/permission based administration
- Teacher course dashboard, enrollments, attendance, assignments, submissions, grading and feedback
- Student dashboard, academic summary, attendance, timetable, results, GPA/CGPA and official transcript PDF
- Course materials and assignment file-link metadata
- Announcements and notification center
- University calendar
- Communities with posts, comments, reactions, polls and attachments
- Events, registration, tickets/check-in and certificates
- Clubs and memberships
- Student service requests
- Fees, payment records and receipts metadata
- Campus services, library loans, hostel rooms/applications, bus routes, cafeteria, emergency contacts, lost & found
- Global search with authenticated access
- Expo mobile navigation for core and campus-service modules
- Render/Gunicorn deployment configuration and GitHub Actions CI

## API

The API is rooted at `/api/v1`.

Important endpoints include:

- `/auth/register`, `/auth/login`, `/auth/logout-all`
- `/profile`, `/profile/verification`
- `/institutions/*/admin/*`
- `/teacher/dashboard`
- `/me/academic-summary`, `/me/transcript`, `/transcript.pdf`
- `/academic-calendar`
- `/groups/*/feed`, `/groups/*/polls`, `/polls/*/vote`
- `/offerings/*/materials`, `/assignments/*/mine`
- `/events/*/ticket`, `/events/*/certificate`
- `/service-requests/advanced`
- `/campus-services`, `/lost-found`, `/library/*`, `/hostel/*`
- `/search/all`
- `/push/devices`

## Deployment

Render start command:

`python -m gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

The production database is configured through `DATABASE_URL`.

## Development

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

The web client is served by Flask from `web/`. The mobile client lives in `mobile/` and accepts `EXPO_PUBLIC_API_URL`.

## Production note

The current app uses SQLAlchemy `create_all()` so newly introduced tables are created automatically. Before changing existing columns or performing destructive schema changes in production, add an Alembic/Flask-Migrate migration and run it during deployment.