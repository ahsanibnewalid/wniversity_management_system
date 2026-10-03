from django.db import models

class LegacyModel(models.Model):
    class Meta:
        abstract=True
        managed=False

class User(LegacyModel):
    id=models.IntegerField(primary_key=True); email=models.CharField(max_length=255,unique=True); password_hash=models.CharField(max_length=255); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="users"
class UserProfile(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(unique=True); full_name=models.CharField(max_length=160); username=models.CharField(max_length=80,unique=True); phone=models.CharField(max_length=40,null=True); address=models.CharField(max_length=255,null=True); bio=models.TextField(null=True); profile_photo_url=models.CharField(max_length=500,null=True); institution_text=models.CharField(max_length=200,null=True); department=models.CharField(max_length=160,null=True); program=models.CharField(max_length=160,null=True); student_id=models.CharField(max_length=100,null=True); is_complete=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="user_profiles"
class AuthToken(LegacyModel):
    id=models.IntegerField(primary_key=True); token=models.CharField(max_length=128,unique=True); user_id=models.IntegerField(); created_at=models.DateTimeField(); revoked=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="auth_tokens"
class Institution(LegacyModel):
    id=models.IntegerField(primary_key=True); name=models.CharField(max_length=200,unique=True); slug=models.CharField(max_length=120,unique=True); kind=models.CharField(max_length=80); address=models.CharField(max_length=255,null=True); website=models.CharField(max_length=500,null=True); description=models.TextField(null=True); owner_id=models.IntegerField()
    class Meta(LegacyModel.Meta): db_table="institutions"
class InstitutionMembership(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); user_id=models.IntegerField(); role=models.CharField(max_length=50); status=models.CharField(max_length=30); student_id=models.CharField(max_length=100,null=True); program=models.CharField(max_length=160,null=True)
    class Meta(LegacyModel.Meta):
        db_table="institution_memberships"
        constraints=[models.UniqueConstraint(fields=["institution_id","user_id"],name="uq_institution_user")]
class Department(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); name=models.CharField(max_length=160); code=models.CharField(max_length=40)
    class Meta(LegacyModel.Meta):
        db_table="departments"; constraints=[models.UniqueConstraint(fields=["institution_id","name"],name="uq_department_name")]
class AcademicSession(LegacyModel):
    id=models.IntegerField(primary_key=True); department_id=models.IntegerField(); name=models.CharField(max_length=80)
    class Meta(LegacyModel.Meta):
        db_table="academic_sessions"; constraints=[models.UniqueConstraint(fields=["department_id","name"],name="uq_session_name")]
class AcademicYear(LegacyModel):
    id=models.IntegerField(primary_key=True); session_id=models.IntegerField(); name=models.CharField(max_length=80)
    class Meta(LegacyModel.Meta):
        db_table="academic_years"; constraints=[models.UniqueConstraint(fields=["session_id","name"],name="uq_year_name")]
class Group(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); department_id=models.IntegerField(null=True); session_id=models.IntegerField(null=True); academic_year_id=models.IntegerField(null=True); name=models.CharField(max_length=180); group_type=models.CharField(max_length=40); description=models.TextField(null=True); is_private=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="groups"
class GroupMembership(LegacyModel):
    id=models.IntegerField(primary_key=True); group_id=models.IntegerField(); user_id=models.IntegerField(); role=models.CharField(max_length=50); status=models.CharField(max_length=30)
    class Meta(LegacyModel.Meta):
        db_table="group_memberships"; constraints=[models.UniqueConstraint(fields=["group_id","user_id"],name="uq_group_user")]
class JoinRequest(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); user_id=models.IntegerField(); department_id=models.IntegerField(null=True); student_id=models.CharField(max_length=100); program=models.CharField(max_length=160); session=models.CharField(max_length=80); academic_year=models.CharField(max_length=80); note=models.TextField(null=True); status=models.CharField(max_length=30); reviewed_by=models.IntegerField(null=True); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="join_requests"
class Post(LegacyModel):
    id=models.IntegerField(primary_key=True); group_id=models.IntegerField(); author_id=models.IntegerField(); post_type=models.CharField(max_length=30); body=models.TextField(); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="posts"
class Comment(LegacyModel):
    id=models.IntegerField(primary_key=True); post_id=models.IntegerField(); author_id=models.IntegerField(); body=models.TextField(); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="comments"
class Reaction(LegacyModel):
    id=models.IntegerField(primary_key=True); post_id=models.IntegerField(); user_id=models.IntegerField(); reaction=models.CharField(max_length=30)
    class Meta(LegacyModel.Meta):
        db_table="reactions"; constraints=[models.UniqueConstraint(fields=["post_id","user_id"],name="uq_post_user_reaction")]
class Notification(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(); kind=models.CharField(max_length=60); title=models.CharField(max_length=200); body=models.TextField(null=True); is_read=models.BooleanField(); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="notifications"

class Faculty(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); name=models.CharField(max_length=255); code=models.CharField(max_length=50); description=models.TextField()
    class Meta(LegacyModel.Meta): db_table="faculty"
class Program(LegacyModel):
    id=models.IntegerField(primary_key=True); department_id=models.IntegerField(); name=models.CharField(max_length=255); code=models.CharField(max_length=50); degree=models.CharField(max_length=100); duration_years=models.IntegerField()
    class Meta(LegacyModel.Meta): db_table="program"
class Semester(LegacyModel):
    id=models.IntegerField(primary_key=True); program_id=models.IntegerField(null=True); name=models.CharField(max_length=100); number=models.IntegerField(); start_date=models.DateField(null=True); end_date=models.DateField(null=True)
    class Meta(LegacyModel.Meta): db_table="semester"
class Course(LegacyModel):
    id=models.IntegerField(primary_key=True); department_id=models.IntegerField(null=True); code=models.CharField(max_length=50); title=models.CharField(max_length=255); credits=models.FloatField(); description=models.TextField()
    class Meta(LegacyModel.Meta): db_table="course"
class CourseOffering(LegacyModel):
    id=models.IntegerField(primary_key=True); course_id=models.IntegerField(); semester_id=models.IntegerField(null=True); teacher_id=models.IntegerField(null=True); section=models.CharField(max_length=50); room=models.CharField(max_length=100); capacity=models.IntegerField(); status=models.CharField(max_length=30)
    class Meta(LegacyModel.Meta): db_table="course_offering"
class Enrollment(LegacyModel):
    id=models.IntegerField(primary_key=True); offering_id=models.IntegerField(); student_id=models.IntegerField(); status=models.CharField(max_length=30); enrolled_at=models.DateTimeField()
    class Meta(LegacyModel.Meta):
        db_table="enrollment"; constraints=[models.UniqueConstraint(fields=["offering_id","student_id"],name="uq_course_student")]
class Attendance(LegacyModel):
    id=models.IntegerField(primary_key=True); offering_id=models.IntegerField(); student_id=models.IntegerField(); date=models.DateField(); status=models.CharField(max_length=20); note=models.TextField()
    class Meta(LegacyModel.Meta):
        db_table="attendance"; constraints=[models.UniqueConstraint(fields=["offering_id","student_id","date"],name="uq_attendance")]
class Assignment(LegacyModel):
    id=models.IntegerField(primary_key=True); offering_id=models.IntegerField(); title=models.CharField(max_length=255); description=models.TextField(); due_at=models.DateTimeField(null=True); max_score=models.FloatField(); attachment_url=models.CharField(max_length=500)
    class Meta(LegacyModel.Meta): db_table="assignment"
class Submission(LegacyModel):
    id=models.IntegerField(primary_key=True); assignment_id=models.IntegerField(); student_id=models.IntegerField(); body=models.TextField(); file_url=models.CharField(max_length=500); score=models.FloatField(null=True); feedback=models.TextField(); submitted_at=models.DateTimeField()
    class Meta(LegacyModel.Meta):
        db_table="submission"; constraints=[models.UniqueConstraint(fields=["assignment_id","student_id"],name="uq_submission")]
class Exam(LegacyModel):
    id=models.IntegerField(primary_key=True); offering_id=models.IntegerField(); title=models.CharField(max_length=255); exam_type=models.CharField(max_length=50); exam_at=models.DateTimeField(null=True); room=models.CharField(max_length=100)
    class Meta(LegacyModel.Meta): db_table="exam"
class Result(LegacyModel):
    id=models.IntegerField(primary_key=True); student_id=models.IntegerField(); course_id=models.IntegerField(); semester_id=models.IntegerField(null=True); grade=models.CharField(max_length=10); grade_point=models.FloatField(); credits=models.FloatField(); published=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="result"
class TimetableEntry(LegacyModel):
    id=models.IntegerField(primary_key=True); offering_id=models.IntegerField(); weekday=models.IntegerField(); start_time=models.CharField(max_length=10); end_time=models.CharField(max_length=10); room=models.CharField(max_length=100)
    class Meta(LegacyModel.Meta): db_table="timetable_entry"


class Event(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(null=True); organizer_id=models.IntegerField(null=True); title=models.CharField(max_length=255); description=models.TextField(); starts_at=models.DateTimeField(null=True); ends_at=models.DateTimeField(null=True); location=models.CharField(max_length=255); event_type=models.CharField(max_length=60); capacity=models.IntegerField(null=True); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="event"
class EventRegistration(LegacyModel):
    id=models.IntegerField(primary_key=True); event_id=models.IntegerField(); user_id=models.IntegerField(); registered_at=models.DateTimeField()
    class Meta(LegacyModel.Meta):
        db_table="event_registration"; constraints=[models.UniqueConstraint(fields=["event_id","user_id"],name="uq_event_user")]
class Club(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); name=models.CharField(max_length=255); description=models.TextField(); logo_url=models.CharField(max_length=500)
    class Meta(LegacyModel.Meta): db_table="club"
class ClubMembership(LegacyModel):
    id=models.IntegerField(primary_key=True); club_id=models.IntegerField(); user_id=models.IntegerField(); role=models.CharField(max_length=40)
    class Meta(LegacyModel.Meta):
        db_table="club_membership"; constraints=[models.UniqueConstraint(fields=["club_id","user_id"],name="uq_club_user")]
class Document(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(null=True); owner_id=models.IntegerField(); title=models.CharField(max_length=255); category=models.CharField(max_length=80); url=models.CharField(max_length=500); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="document"
class ServiceRequest(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(); institution_id=models.IntegerField(null=True); request_type=models.CharField(max_length=100); details=models.TextField(); status=models.CharField(max_length=30); response=models.TextField(); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="service_request"
class Fee(LegacyModel):
    id=models.IntegerField(primary_key=True); student_id=models.IntegerField(); institution_id=models.IntegerField(null=True); title=models.CharField(max_length=255); amount=models.FloatField(); due_date=models.DateField(null=True); status=models.CharField(max_length=30)
    class Meta(LegacyModel.Meta): db_table="fee"
class Message(LegacyModel):
    id=models.IntegerField(primary_key=True); sender_id=models.IntegerField(); recipient_id=models.IntegerField(); body=models.TextField(); read_at=models.DateTimeField(null=True); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="message"
class Poll(LegacyModel):
    id=models.IntegerField(primary_key=True); post_id=models.IntegerField(unique=True); question=models.CharField(max_length=500)
    class Meta(LegacyModel.Meta): db_table="poll"
class PollOption(LegacyModel):
    id=models.IntegerField(primary_key=True); poll_id=models.IntegerField(); label=models.CharField(max_length=255); position=models.IntegerField()
    class Meta(LegacyModel.Meta): db_table="poll_option"
class PollVote(LegacyModel):
    id=models.IntegerField(primary_key=True); option_id=models.IntegerField(); user_id=models.IntegerField()
    class Meta(LegacyModel.Meta):
        db_table="poll_vote"; constraints=[models.UniqueConstraint(fields=["option_id","user_id"],name="uq_poll_vote")]
class PostAttachment(LegacyModel):
    id=models.IntegerField(primary_key=True); post_id=models.IntegerField(); name=models.CharField(max_length=255); url=models.CharField(max_length=1000); mime_type=models.CharField(max_length=120)
    class Meta(LegacyModel.Meta): db_table="post_attachment"
class AcademicCalendarItem(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); department_id=models.IntegerField(null=True); title=models.CharField(max_length=255); kind=models.CharField(max_length=60); starts_at=models.DateTimeField(null=True); ends_at=models.DateTimeField(null=True); description=models.TextField(); location=models.CharField(max_length=255); audience=models.CharField(max_length=80)
    class Meta(LegacyModel.Meta): db_table="academic_calendar_item"
class Announcement(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); author_id=models.IntegerField(); title=models.CharField(max_length=255); body=models.TextField(); audience=models.CharField(max_length=50); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="announcement"
class AnnouncementTarget(LegacyModel):
    id=models.IntegerField(primary_key=True); announcement_id=models.IntegerField(); group_id=models.IntegerField()
    class Meta(LegacyModel.Meta): db_table="announcement_target"
class EventTicket(LegacyModel):
    id=models.IntegerField(primary_key=True); event_id=models.IntegerField(); user_id=models.IntegerField(); code=models.CharField(max_length=160,unique=True); checked_in=models.BooleanField(); issued_at=models.DateTimeField()
    class Meta(LegacyModel.Meta):
        db_table="event_ticket"; constraints=[models.UniqueConstraint(fields=["event_id","user_id"],name="uq_event_ticket")]
class Certificate(LegacyModel):
    id=models.IntegerField(primary_key=True); event_id=models.IntegerField(); user_id=models.IntegerField(); certificate_no=models.CharField(max_length=160,unique=True); title=models.CharField(max_length=255); issued_at=models.DateTimeField()
    class Meta(LegacyModel.Meta):
        db_table="certificate"; constraints=[models.UniqueConstraint(fields=["event_id","user_id"],name="uq_event_certificate")]
class StudentRequest(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(); institution_id=models.IntegerField(null=True); request_type=models.CharField(max_length=100); details=models.TextField(); status=models.CharField(max_length=30); response=models.TextField(); tracking_no=models.CharField(max_length=80,unique=True); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="student_request"
class CampusService(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); kind=models.CharField(max_length=50); name=models.CharField(max_length=255); description=models.TextField(); location=models.CharField(max_length=255); contact=models.CharField(max_length=255); hours=models.CharField(max_length=255); status=models.CharField(max_length=30)
    class Meta(LegacyModel.Meta): db_table="campus_service"
class LostFoundItem(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); reporter_id=models.IntegerField(); item_type=models.CharField(max_length=30); title=models.CharField(max_length=255); description=models.TextField(); location=models.CharField(max_length=255); contact=models.CharField(max_length=255); status=models.CharField(max_length=30); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="lost_found_item"
class EmergencyContact(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); name=models.CharField(max_length=255); phone=models.CharField(max_length=80); category=models.CharField(max_length=80); location=models.CharField(max_length=255)
    class Meta(LegacyModel.Meta): db_table="emergency_contact"
class BusRoute(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); name=models.CharField(max_length=255); stops=models.TextField(); departure_times=models.TextField(); active=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="bus_route"
class HostelRoom(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); building=models.CharField(max_length=120); room_no=models.CharField(max_length=50); capacity=models.IntegerField(); status=models.CharField(max_length=30); occupant_id=models.IntegerField(null=True)
    class Meta(LegacyModel.Meta): db_table="hostel_room"
class LibraryItem(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); title=models.CharField(max_length=255); author=models.CharField(max_length=255); isbn=models.CharField(max_length=80); category=models.CharField(max_length=120); copies=models.IntegerField(); available_copies=models.IntegerField()
    class Meta(LegacyModel.Meta): db_table="library_item"
class LibraryLoan(LegacyModel):
    id=models.IntegerField(primary_key=True); item_id=models.IntegerField(); user_id=models.IntegerField(); borrowed_at=models.DateTimeField(); due_at=models.DateTimeField(null=True); returned_at=models.DateTimeField(null=True)
    class Meta(LegacyModel.Meta): db_table="library_loan"
class CafeteriaItem(LegacyModel):
    id=models.IntegerField(primary_key=True); institution_id=models.IntegerField(); name=models.CharField(max_length=255); category=models.CharField(max_length=100); price=models.FloatField(); available=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="cafeteria_item"
class VerificationToken(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(); token=models.CharField(max_length=180,unique=True); purpose=models.CharField(max_length=40); expires_at=models.DateTimeField(); used=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="verification_token"
class PasswordResetToken(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(); token=models.CharField(max_length=180,unique=True); expires_at=models.DateTimeField(); used=models.BooleanField()
    class Meta(LegacyModel.Meta): db_table="password_reset_token"
class CourseMaterial(LegacyModel):
    id=models.IntegerField(primary_key=True); offering_id=models.IntegerField(); teacher_id=models.IntegerField(); title=models.CharField(max_length=255); description=models.TextField(); url=models.CharField(max_length=1000); mime_type=models.CharField(max_length=120); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="course_material"
class PushDevice(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(); token=models.CharField(max_length=500,unique=True); platform=models.CharField(max_length=30); active=models.BooleanField(); created_at=models.DateTimeField()
    class Meta(LegacyModel.Meta): db_table="push_device"
class UserVerification(LegacyModel):
    id=models.IntegerField(primary_key=True); user_id=models.IntegerField(unique=True); verified=models.BooleanField(); verified_at=models.DateTimeField(null=True)
    class Meta(LegacyModel.Meta): db_table="user_verification"
class AnnouncementRead(LegacyModel):
    id=models.IntegerField(primary_key=True); announcement_id=models.IntegerField(); user_id=models.IntegerField(); read_at=models.DateTimeField()
    class Meta(LegacyModel.Meta):
        db_table="announcement_read"; constraints=[models.UniqueConstraint(fields=["announcement_id","user_id"],name="uq_announcement_read")]
