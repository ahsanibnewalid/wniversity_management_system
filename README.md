# CampusHub 🎓

<p align="center"><strong>University ERP + Learning Platform + Campus Social Network + Messaging + Campus Services</strong></p>

<p align="center"><img alt="Django" src="https://img.shields.io/badge/Backend-Django-092E20?logo=django&logoColor=white"> <img alt="PostgreSQL" src="https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white"> <img alt="Web" src="https://img.shields.io/badge/Web-Responsive-2ea44f"> <img alt="Mobile" src="https://img.shields.io/badge/Mobile-Expo%20%2F%20React%20Native-000020?logo=expo&logoColor=white"></p>

## Overview

CampusHub is an API-first university platform combining academic management, campus communication, community interaction, and student services in one system.

## Product Vision

**CampusHub = University ERP + Learning Management + Student Portal + Parent Portal + Campus Social Network + Messaging + Campus Services + Careers + Institutional Administration**

## Core Areas

### 🎓 Academic
- Institutions, departments, programs, semesters, sessions, and academic years
- Courses, offerings, enrollment, attendance, assignments, submissions, exams, results, and timetables
- Academic documents and certificates

### 🏫 Administration
- Institution and department management
- Role-based access and tenant-aware permissions
- Membership and approval workflows
- Announcements, documents, verification, and password reset
- Platform administration

### 🌐 Campus Social
- Social-style home feed
- Communities and groups
- Posts, comments, reactions, polls, notifications, and discovery

### 💬 Communication
- Direct and group conversations
- Course, department, university, and support channels
- Threads, reactions, search, unread state, mute, archive, pin, reporting, and moderation

### 🚌 Campus Life
- Events and registrations
- Clubs and communities
- Campus services
- Lost & found
- Emergency contacts
- Bus routes, hostel, library, and cafeteria

### 💼 Careers & Collaboration
The platform is designed to expand toward internships, jobs, recruiter communication, university/company collaboration, and research workflows.

## Architecture

    CampusHub
       ├── Django API
       ├── Responsive Web Client
       ├── Expo / React Native Client
       └── PostgreSQL

The Django compatibility layer preserves the existing `/api/v1` API contract and legacy PostgreSQL table structure where compatibility is required.

## Local Development

### Backend

    cd django_backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py check
    python manage.py runserver

### Mobile

    cd mobile
    npm install
    npx expo start

For a native Android build:

    npx expo prebuild
    cd android
    ./gradlew assembleDebug

## Production

The repository includes production-oriented Django/Gunicorn and Render configuration with secure settings, PostgreSQL support, CORS configuration, HTTPS hardening, and SMTP support for verification/password-reset email.

**Database compatibility:** do not run destructive Django migrations against an existing production database without a planned migration and backup strategy.

## Testing

Automated tests and CI checks cover backend behavior, Django deployment checks, and web JavaScript validation. Staging/live smoke checks are available under `django_backend/scripts/smoke.sh`.

## Security

Authentication, bearer-token support, role-based permissions, tenant-aware authorization, verification/password-reset flows, moderation controls, and production security settings are part of the platform architecture.

## Payments

CampusHub intentionally does **not** implement payment gateways or transaction processing. Fee records may exist as informational data, but checkout, bank integration, payment webhooks, and transaction processing are outside the current scope.

## Project Status

🚧 **Active development**

## Contributing

Issues, feature proposals, documentation improvements, and pull requests are welcome. Please preserve the `/api/v1` compatibility contract when changing backend behavior.

## License

See the repository license file for applicable terms.
