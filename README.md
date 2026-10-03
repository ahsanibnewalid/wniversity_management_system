# CampusHub

API-first University Management + Community platform.

## Architecture
- backend/ — Flask API, database models, routes and services
- web/ — web client foundation
- mobile/ — React Native/Expo client foundation
- tests/ — automated tests
- PostgreSQL on Render; SQLite for local development

## Product workflow
Register → complete profile → apply to institution with student ID, department, program, session and academic year → institution admin reviews → approved membership → institution, department, session and academic-year communities.

## Community hierarchy
Institution → Department → Session → Academic Year.

Groups support posts, questions, comments and reactions. The permission model is designed for institution owners/admins/principals, department chairmen/admins, media managers and class representatives.

## Local
python -m venv .venv
pip install -r requirements.txt
python -c "from backend.app import app; app.run(debug=True)"

Health: http://127.0.0.1:5000/healthz

## Render
Build: pip install -r requirements.txt
Start: gunicorn "backend.app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
Health check: /healthz

Password reset email delivery requires `SMTP_HOST` and `SMTP_FROM` to be set on the service. Set `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and the TLS options to match the provider. Reset credentials are sent only by email and are never included in API responses; requests return `503 password_reset_delivery_unavailable` when delivery is not configured or fails.

Set `PLATFORM_ADMIN_EMAILS` in Render's environment settings to a comma-separated list of trusted operator email addresses to enable the centralized platform administration console. Keep this list limited to authorized CampusHub operators; institution roles do not grant platform-wide access. Platform administrators can monitor tenant counts, search users and memberships, add members to universities, assign tenant roles, suspend memberships, and transfer institution ownership. Remove a platform operator by removing their email from `PLATFORM_ADMIN_EMAILS`.

Platform administration endpoints are rooted at `/api/v1/platform/admin`. The role is controlled by this server-side allowlist and cannot be granted by users or institution administrators.

## Communication Center

The web and mobile clients use `/api/v1/communications` for tenant-scoped direct chats, group conversations, course discussions, department and university channels, and student-support requests. Course channels can be configured for teacher-only official posts; university announcement channels are restricted to institution managers. Existing institution announcements support `all`, `students`, `teachers`, `staff`, and `admins` audiences.

Communication features include threaded replies, link attachments, message reactions, message search, unread counts/read timestamps, per-user mute/archive/pin settings, user blocking, message reports, and manager/teacher moderation queues. Muted conversations do not create new in-app message notifications. Conversation access is removed when the user's institution membership is suspended.

Attachments are currently links to externally hosted files; CampusHub does not yet upload or store file contents. In-app notifications are supported, but email/push delivery for new messages, parent/company accounts, and configurable retention schedules are not implemented. Official posts are immutable through the current API and include author/timestamp metadata; agree institution retention rules before adding automated deletion.

The communication tables are created with the application's existing SQLAlchemy `create_all` startup path. New deployments therefore need no new package or environment setting.

## Mobile
cd mobile
npm install
npx expo start

When native Android/iOS projects are needed:
npx expo prebuild
cd android
gradlew assembleDebug

The resulting debug APK is generated under android/app/build/outputs/apk/debug/.


## Implementation status
The full-platform implementation is being expanded across the API, web and mobile clients.
