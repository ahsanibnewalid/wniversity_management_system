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
