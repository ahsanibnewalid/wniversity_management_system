# Django migration status

Branch: django-migration

## Implemented

- Django 5.2 + Django REST Framework foundation.
- PostgreSQL configuration through the existing DATABASE_URL.
- Compatibility ORM for the current CampusHub tables with managed = False.
- Existing integer primary keys and table names preserved.
- Existing bearer token table used directly.
- Existing Werkzeug password hashes accepted directly.
- Auth/register/login/me/logout/logout-all compatibility.
- Institution listing/creation/join and current memberships.
- Profile read/update.
- /healthz.

## Legacy model inventory captured

Accounts: User, UserProfile, AuthToken, VerificationToken, PasswordResetToken, UserVerification, PushDevice.

Institution/academics: Institution, InstitutionMembership, Department, AcademicSession, AcademicYear, Faculty, Program, Semester, Course, CourseOffering, Enrollment, Attendance, Assignment, Submission, Exam, Result, TimetableEntry, CourseMaterial.

Community: Group, GroupMembership, Post, Comment, Reaction, Poll, PollOption, PollVote, PostAttachment.

Communication/platform: Message, Notification, Announcement, AnnouncementTarget, AnnouncementRead.

Events: Event, EventRegistration, EventTicket, Certificate, Club, ClubMembership.

Campus/services: Document, ServiceRequest, Fee, StudentRequest, CampusService, LostFoundItem, EmergencyContact, BusRoute, HostelRoom, LibraryItem, LibraryLoan, CafeteriaItem, AcademicCalendarItem.

## Still to migrate

The remaining Flask endpoint behavior is intentionally not deleted or silently replaced. Academic, community, event/campus, notification, PDF, search, teacher, and institution-admin endpoints remain on the Flask implementation until their Django equivalents are validated.

## Cutover rule

Do not point production at this branch yet. The safe sequence is:
1. Validate against a PostgreSQL backup/staging database.
2. Port the remaining endpoints while keeping response JSON/status codes unchanged.
3. Run web/mobile integration tests.
4. Cut production traffic to Django.
5. Remove Flask only after all API routes have Django coverage.
6. Then change managed = False models to Django-owned models and introduce normal migrations.
