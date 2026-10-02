from datetime import datetime, timezone
from flask import request, jsonify
from backend.core import db, Department, Institution, InstitutionMembership, Notification
from backend.api import login_required, institution_manager

class Faculty(db.Model):
    id=db.Column(db.Integer,primary_key=True); institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"),nullable=False); name=db.Column(db.String(255),nullable=False); code=db.Column(db.String(50),default=""); description=db.Column(db.Text,default="")
class Program(db.Model):
    id=db.Column(db.Integer,primary_key=True); department_id=db.Column(db.Integer,db.ForeignKey("departments.id"),nullable=False); name=db.Column(db.String(255),nullable=False); code=db.Column(db.String(50),default=""); degree=db.Column(db.String(100),default=""); duration_years=db.Column(db.Integer,default=4)
class Semester(db.Model):
    id=db.Column(db.Integer,primary_key=True); program_id=db.Column(db.Integer,db.ForeignKey("program.id")); name=db.Column(db.String(100),nullable=False); number=db.Column(db.Integer,default=1); start_date=db.Column(db.Date); end_date=db.Column(db.Date)
class Course(db.Model):
    id=db.Column(db.Integer,primary_key=True); department_id=db.Column(db.Integer,db.ForeignKey("departments.id")); code=db.Column(db.String(50),nullable=False); title=db.Column(db.String(255),nullable=False); credits=db.Column(db.Float,default=3); description=db.Column(db.Text,default="")
class CourseOffering(db.Model):
    id=db.Column(db.Integer,primary_key=True); course_id=db.Column(db.Integer,db.ForeignKey("course.id"),nullable=False); semester_id=db.Column(db.Integer,db.ForeignKey("semester.id")); teacher_id=db.Column(db.Integer,db.ForeignKey("users.id")); section=db.Column(db.String(50),default="A"); room=db.Column(db.String(100),default=""); capacity=db.Column(db.Integer,default=50); status=db.Column(db.String(30),default="open")
class Enrollment(db.Model):
    id=db.Column(db.Integer,primary_key=True); offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id"),nullable=False); student_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False); status=db.Column(db.String(30),default="enrolled"); enrolled_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    __table_args__=(db.UniqueConstraint("offering_id","student_id",name="uq_course_student"),)
class Attendance(db.Model):
    id=db.Column(db.Integer,primary_key=True); offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id"),nullable=False); student_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False); date=db.Column(db.Date,nullable=False); status=db.Column(db.String(20),default="present"); note=db.Column(db.Text,default="")
    __table_args__=(db.UniqueConstraint("offering_id","student_id","date",name="uq_attendance"),)
class Assignment(db.Model):
    id=db.Column(db.Integer,primary_key=True); offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id"),nullable=False); title=db.Column(db.String(255),nullable=False); description=db.Column(db.Text,default=""); due_at=db.Column(db.DateTime(timezone=True)); max_score=db.Column(db.Float,default=100); attachment_url=db.Column(db.String(500),default="")
class Submission(db.Model):
    id=db.Column(db.Integer,primary_key=True); assignment_id=db.Column(db.Integer,db.ForeignKey("assignment.id"),nullable=False); student_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False); body=db.Column(db.Text,default=""); file_url=db.Column(db.String(500),default=""); score=db.Column(db.Float); feedback=db.Column(db.Text,default=""); submitted_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    __table_args__=(db.UniqueConstraint("assignment_id","student_id",name="uq_submission"),)
class Exam(db.Model):
    id=db.Column(db.Integer,primary_key=True); offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id"),nullable=False); title=db.Column(db.String(255),nullable=False); exam_type=db.Column(db.String(50),default="final"); exam_at=db.Column(db.DateTime(timezone=True)); room=db.Column(db.String(100),default="")
class Result(db.Model):
    id=db.Column(db.Integer,primary_key=True); student_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False); course_id=db.Column(db.Integer,db.ForeignKey("course.id"),nullable=False); semester_id=db.Column(db.Integer,db.ForeignKey("semester.id")); grade=db.Column(db.String(10),nullable=False); grade_point=db.Column(db.Float,default=0); credits=db.Column(db.Float,default=0); published=db.Column(db.Boolean,default=False)
class TimetableEntry(db.Model):
    id=db.Column(db.Integer,primary_key=True); offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id"),nullable=False); weekday=db.Column(db.Integer,default=0); start_time=db.Column(db.String(10),default="09:00"); end_time=db.Column(db.String(10),default="10:00"); room=db.Column(db.String(100),default="")

def data(x):
    return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def register(app):
    @app.post("/api/v1/institutions/<int:iid>/faculties")
    @login_required
    def add_faculty(iid):
        if not institution_manager(iid):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=Faculty(institution_id=iid,name=d.get("name",""),code=d.get("code",""));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/institutions/<int:iid>/faculties")
    def faculties(iid):return jsonify(items=[data(x) for x in Faculty.query.filter_by(institution_id=iid).all()])
    @app.post("/api/v1/departments/<int:did>/programs")
    @login_required
    def add_program(did):
        dep=db.get_or_404(Department,did)
        if not institution_manager(dep.institution_id):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=Program(department_id=did,name=d.get("name",""),code=d.get("code",""),degree=d.get("degree",""),duration_years=d.get("duration_years",4));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/departments/<int:did>/programs")
    def programs(did):return jsonify(items=[data(x) for x in Program.query.filter_by(department_id=did).all()])
    @app.post("/api/v1/departments/<int:did>/courses")
    @login_required
    def add_course(did):
        dep=db.get_or_404(Department,did)
        if not institution_manager(dep.institution_id):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=Course(department_id=did,code=d.get("code",""),title=d.get("title",""),credits=float(d.get("credits",3)),description=d.get("description",""));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/departments/<int:did>/courses")
    def courses(did):return jsonify(items=[data(x) for x in Course.query.filter_by(department_id=did).all()])
    @app.post("/api/v1/courses/<int:cid>/offerings")
    @login_required
    def add_offering(cid):
        c=db.get_or_404(Course,cid);dep=db.get_or_404(Department,c.department_id)
        if not institution_manager(dep.institution_id):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=CourseOffering(course_id=cid,semester_id=d.get("semester_id"),teacher_id=d.get("teacher_id") or request.current_user.id,section=d.get("section","A"),room=d.get("room",""),capacity=d.get("capacity",50));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/courses/<int:cid>/offerings")
    def offerings(cid):return jsonify(items=[data(x) for x in CourseOffering.query.filter_by(course_id=cid).all()])
    @app.post("/api/v1/offerings/<int:oid>/enroll")
    @login_required
    def enroll(oid):
        d=request.get_json() or {};sid=int(d.get("student_id",request.current_user.id))
        if sid!=request.current_user.id:return jsonify(error="forbidden"),403
        if Enrollment.query.filter_by(offering_id=oid,student_id=sid).first():return jsonify(error="already_enrolled"),409
        x=Enrollment(offering_id=oid,student_id=sid);db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/me/enrollments")
    @login_required
    def my_enrollments():return jsonify(items=[data(x) for x in Enrollment.query.filter_by(student_id=request.current_user.id,status="enrolled").all()])
    @app.post("/api/v1/offerings/<int:oid>/attendance")
    @login_required
    def save_attendance(oid):
        o=db.get_or_404(CourseOffering,oid)
        if o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        d=request.get_json() or {};day=datetime.fromisoformat(d.get("date",datetime.now().date().isoformat())).date()
        for row in d.get("records",[]):
            x=Attendance.query.filter_by(offering_id=oid,student_id=row["student_id"],date=day).first() or Attendance(offering_id=oid,student_id=row["student_id"],date=day)
            x.status=row.get("status","present");x.note=row.get("note","");db.session.add(x)
        db.session.commit();return jsonify(status="saved")
    @app.get("/api/v1/me/attendance")
    @login_required
    def my_attendance():return jsonify(items=[data(x) for x in Attendance.query.filter_by(student_id=request.current_user.id).order_by(Attendance.date.desc()).all()])
    @app.post("/api/v1/offerings/<int:oid>/assignments")
    @login_required
    def add_assignment(oid):
        o=db.get_or_404(CourseOffering,oid)
        if o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        d=request.get_json() or {};due=datetime.fromisoformat(d["due_at"].replace("Z","+00:00")) if d.get("due_at") else None;x=Assignment(offering_id=oid,title=d.get("title",""),description=d.get("description",""),due_at=due,max_score=d.get("max_score",100),attachment_url=d.get("attachment_url",""));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/offerings/<int:oid>/assignments")
    @login_required
    def assignments(oid):return jsonify(items=[data(x) for x in Assignment.query.filter_by(offering_id=oid).all()])
    @app.post("/api/v1/assignments/<int:aid>/submit")
    @login_required
    def submit(aid):
        d=request.get_json() or {};x=Submission.query.filter_by(assignment_id=aid,student_id=request.current_user.id).first() or Submission(assignment_id=aid,student_id=request.current_user.id)
        x.body=d.get("body","");x.file_url=d.get("file_url","");x.submitted_at=datetime.now(timezone.utc);db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.post("/api/v1/submissions/<int:sid>/grade")
    @login_required
    def grade(sid):
        x=db.get_or_404(Submission,sid);a=db.get_or_404(Assignment,x.assignment_id);o=db.get_or_404(CourseOffering,a.offering_id)
        if o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        d=request.get_json() or {};x.score=d.get("score");x.feedback=d.get("feedback","");db.session.commit();return jsonify(data(x))
    @app.post("/api/v1/offerings/<int:oid>/exams")
    @login_required
    def add_exam(oid):
        o=db.get_or_404(CourseOffering,oid)
        if o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        d=request.get_json() or {};at=datetime.fromisoformat(d["exam_at"].replace("Z","+00:00")) if d.get("exam_at") else None;x=Exam(offering_id=oid,title=d.get("title",""),exam_type=d.get("exam_type","final"),exam_at=at,room=d.get("room",""));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/offerings/<int:oid>/exams")
    @login_required
    def exams(oid):return jsonify(items=[data(x) for x in Exam.query.filter_by(offering_id=oid).all()])
    @app.get("/api/v1/me/results")
    @login_required
    def results():return jsonify(items=[data(x) for x in Result.query.filter_by(student_id=request.current_user.id,published=True).all()])
    @app.get("/api/v1/me/transcript")
    @login_required
    def transcript():
        rows=Result.query.filter_by(student_id=request.current_user.id,published=True).all();credits=sum(x.credits for x in rows);points=sum(x.credits*x.grade_point for x in rows)
        return jsonify(results=[data(x) for x in rows],credits=credits,cgpa=round(points/credits,2) if credits else 0)
    @app.post("/api/v1/students/<int:sid>/results")
    @login_required
    def add_result(sid):
        d=request.get_json() or {}; course=db.session.get(Course,d.get("course_id")); dep=db.session.get(Department,course.department_id) if course else None
        if not dep or not institution_manager(dep.institution_id):return jsonify(error="forbidden"),403
        x=Result(student_id=sid,course_id=d["course_id"],semester_id=d.get("semester_id"),grade=d["grade"],grade_point=d.get("grade_point",0),credits=d.get("credits",0),published=d.get("published",False));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.post("/api/v1/offerings/<int:oid>/timetable")
    @login_required
    def add_timetable(oid):
        o=db.get_or_404(CourseOffering,oid)
        if o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=TimetableEntry(offering_id=oid,weekday=d.get("weekday",0),start_time=d.get("start_time","09:00"),end_time=d.get("end_time","10:00"),room=d.get("room",""));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/me/timetable")
    @login_required
    def timetable():
        ids=[x.offering_id for x in Enrollment.query.filter_by(student_id=request.current_user.id,status="enrolled").all()]
        return jsonify(items=[data(x) for x in TimetableEntry.query.filter(TimetableEntry.offering_id.in_(ids)).order_by(TimetableEntry.weekday,TimetableEntry.start_time).all()] if ids else [])
