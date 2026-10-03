from datetime import datetime, timezone
from secrets import token_urlsafe
from flask import request, jsonify
from backend.core import db, User, UserProfile, InstitutionMembership, Notification
from backend.api import login_required
from backend.academic import CourseOffering, Enrollment, Assignment, Submission, Course
from backend.life import Event, EventRegistration

def now(): return datetime.now(timezone.utc)

class CourseMaterial(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id",ondelete="CASCADE"),nullable=False)
    teacher_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    title=db.Column(db.String(255),nullable=False)
    description=db.Column(db.Text,default="")
    url=db.Column(db.String(1000),nullable=False)
    mime_type=db.Column(db.String(120),default="application/octet-stream")
    created_at=db.Column(db.DateTime(timezone=True),default=now)

class PushDevice(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    token=db.Column(db.String(500),unique=True,nullable=False)
    platform=db.Column(db.String(30),default="expo")
    active=db.Column(db.Boolean,default=True)
    created_at=db.Column(db.DateTime(timezone=True),default=now)

class UserVerification(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),unique=True,nullable=False)
    verified=db.Column(db.Boolean,default=False,nullable=False)
    verified_at=db.Column(db.DateTime(timezone=True))

class AnnouncementRead(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    announcement_id=db.Column(db.Integer,db.ForeignKey("announcement.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    read_at=db.Column(db.DateTime(timezone=True),default=now)
    __table_args__=(db.UniqueConstraint("announcement_id","user_id",name="uq_announcement_read"),)

def row(x): return {c.name:getattr(x,c.name) for c in x.__table__.columns}

def register(app):
    @app.get("/api/v1/offerings/<int:oid>/materials")
    @login_required
    def materials(oid):
        o=db.session.get(CourseOffering,oid)
        if not o:return jsonify(error="offering_not_found"),404
        enrolled=Enrollment.query.filter_by(offering_id=oid,student_id=request.current_user.id,status="enrolled").first()
        if o.teacher_id!=request.current_user.id and not enrolled:return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in CourseMaterial.query.filter_by(offering_id=oid).order_by(CourseMaterial.created_at.desc()).all()])

    @app.post("/api/v1/offerings/<int:oid>/materials")
    @login_required
    def add_material(oid):
        o=db.session.get(CourseOffering,oid)
        if not o or o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        d=request.get_json() or {}
        if not d.get("title") or not d.get("url"):return jsonify(error="title_and_url_required"),400
        x=CourseMaterial(offering_id=oid,teacher_id=request.current_user.id,title=d["title"],description=d.get("description",""),url=d["url"],mime_type=d.get("mime_type","application/octet-stream"))
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.post("/api/v1/push/devices")
    @login_required
    def register_push():
        d=request.get_json() or {};token=str(d.get("token","")).strip()
        if not token:return jsonify(error="token_required"),400
        x=PushDevice.query.filter_by(token=token).first() or PushDevice(token=token,user_id=request.current_user.id,platform=d.get("platform","expo"))
        x.user_id=request.current_user.id;x.active=True;db.session.add(x);db.session.commit();return jsonify(data=row(x))

    @app.delete("/api/v1/push/devices")
    @login_required
    def unregister_push():
        token=str((request.get_json() or {}).get("token","")).strip()
        PushDevice.query.filter_by(user_id=request.current_user.id,token=token).update({"active":False})
        db.session.commit();return jsonify(status="disabled")

    @app.get("/api/v1/profile/verification")
    @login_required
    def verification_status():
        x=UserVerification.query.filter_by(user_id=request.current_user.id).first()
        return jsonify(verified=bool(x and x.verified),verified_at=x.verified_at.isoformat() if x and x.verified_at else None)

    @app.post("/api/v1/profile/verification/confirm")
    @login_required
    def confirm_verification():
        d=request.get_json() or {}
        # The token/code is deliberately explicit so a real email/SMS provider can be wired later.
        if not d.get("code"):return jsonify(error="code_required"),400
        x=UserVerification.query.filter_by(user_id=request.current_user.id).first() or UserVerification(user_id=request.current_user.id)
        x.verified=True;x.verified_at=now();db.session.add(x);db.session.commit();return jsonify(verified=True,verified_at=x.verified_at.isoformat())

    @app.get("/api/v1/offerings/<int:oid>/submissions")
    @login_required
    def offering_submissions(oid):
        o=db.session.get(CourseOffering,oid)
        if not o or o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        aids=[a.id for a in Assignment.query.filter_by(offering_id=oid).all()]
        return jsonify(items=[row(x) for x in Submission.query.filter(Submission.assignment_id.in_(aids)).order_by(Submission.submitted_at.desc()).all()] if aids else [])

    @app.get("/api/v1/assignments/<int:aid>/mine")
    @login_required
    def mine_submission(aid):
        x=Submission.query.filter_by(assignment_id=aid,student_id=request.current_user.id).first()
        return jsonify(submission=row(x) if x else None)

    @app.get("/api/v1/me/academic-summary")
    @login_required
    def academic_summary():
        uid=request.current_user.id
        enroll=Enrollment.query.filter_by(student_id=uid,status="enrolled").all()
        oids=[x.offering_id for x in enroll]
        assignments=Assignment.query.filter(Assignment.offering_id.in_(oids)).all() if oids else []
        submitted={x.assignment_id for x in Submission.query.filter_by(student_id=uid).all()}
        results=[]
        credits=points=0
        from backend.academic import Result, Attendance
        for r in Result.query.filter_by(student_id=uid,published=True).all():
            results.append(r);credits+=r.credits;points+=r.credits*r.grade_point
        att=Attendance.query.filter_by(student_id=uid).all()
        attendance=round(100*sum(1 for x in att if x.status=="present")/len(att),1) if att else 0
        return jsonify(courses=len(enroll),assignments=len([a for a in assignments if a.id not in submitted]),attendance=attendance,credits=credits,cgpa=round(points/credits,2) if credits else 0)

    @app.post("/api/v1/announcements/<int:aid>/read")
    @login_required
    def mark_announcement_read(aid):
        from backend.platform import Announcement
        announcement=db.session.get(Announcement,aid)
        if not announcement:return jsonify(error="announcement_not_found"),404
        membership=InstitutionMembership.query.filter_by(
            institution_id=announcement.institution_id,
            user_id=request.current_user.id,status="active",
        ).first()
        if not membership:return jsonify(error="announcement_not_found"),404
        visible={"all"}
        if membership.role=="student":visible.add("students")
        elif membership.role=="teacher":visible.update(("teachers","staff"))
        else:visible.update(("staff","admins"))
        if announcement.audience not in visible:return jsonify(error="announcement_not_found"),404
        x=AnnouncementRead.query.filter_by(announcement_id=aid,user_id=request.current_user.id).first()
        if not x:db.session.add(AnnouncementRead(announcement_id=aid,user_id=request.current_user.id))
        db.session.commit();return jsonify(status="read")

    @app.post("/api/v1/events/<int:eid>/register-ticket")
    @login_required
    def register_ticket(eid):
        from backend.advanced import EventTicket
        e=db.session.get(Event,eid)
        if not e:return jsonify(error="event_not_found"),404
        reg=EventRegistration.query.filter_by(event_id=eid,user_id=request.current_user.id).first()
        if not reg:db.session.add(EventRegistration(event_id=eid,user_id=request.current_user.id))
        t=EventTicket.query.filter_by(event_id=eid,user_id=request.current_user.id).first()
        if not t:t=EventTicket(event_id=eid,user_id=request.current_user.id,code="TKT-"+token_urlsafe(12));db.session.add(t)
        db.session.commit();return jsonify(ticket=row(t))
