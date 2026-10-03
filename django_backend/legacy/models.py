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
