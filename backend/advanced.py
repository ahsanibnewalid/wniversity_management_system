from datetime import datetime, timezone, timedelta
from io import BytesIO
from secrets import token_urlsafe
from flask import request, jsonify, send_file
from werkzeug.security import generate_password_hash
from backend.core import (
    db, User, UserProfile, AuthToken, Institution, InstitutionMembership,
    Department, AcademicSession, AcademicYear, Group, GroupMembership,
    Post, Comment, Reaction, Notification
)
from backend.api import login_required
from backend.academic import Faculty, Program, Semester, Course, CourseOffering, Enrollment, Attendance, Assignment, Submission, Result, Exam, TimetableEntry
from backend.life import Event, EventRegistration, Club, ClubMembership, Document, ServiceRequest, Fee, Payment

def now():
    return datetime.now(timezone.utc)

def utc_dt(value):
    if value is None:return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

class Poll(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    post_id=db.Column(db.Integer,db.ForeignKey("posts.id",ondelete="CASCADE"),unique=True,nullable=False)
    question=db.Column(db.String(500),nullable=False)

class PollOption(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    poll_id=db.Column(db.Integer,db.ForeignKey("poll.id",ondelete="CASCADE"),nullable=False)
    label=db.Column(db.String(255),nullable=False)
    position=db.Column(db.Integer,default=0)

class PollVote(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    option_id=db.Column(db.Integer,db.ForeignKey("poll_option.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    __table_args__=(db.UniqueConstraint("option_id","user_id",name="uq_poll_vote"),)

class PostAttachment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    post_id=db.Column(db.Integer,db.ForeignKey("posts.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(255),nullable=False)
    url=db.Column(db.String(1000),nullable=False)
    mime_type=db.Column(db.String(120),default="application/octet-stream")

class AcademicCalendarItem(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    department_id=db.Column(db.Integer,db.ForeignKey("departments.id"))
    title=db.Column(db.String(255),nullable=False)
    kind=db.Column(db.String(60),default="event",nullable=False)
    starts_at=db.Column(db.DateTime(timezone=True))
    ends_at=db.Column(db.DateTime(timezone=True))
    description=db.Column(db.Text,default="")
    location=db.Column(db.String(255),default="")
    audience=db.Column(db.String(80),default="all")

class AnnouncementTarget(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    announcement_id=db.Column(db.Integer,db.ForeignKey("announcement.id",ondelete="CASCADE"),nullable=False)
    group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"))

class EventTicket(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    event_id=db.Column(db.Integer,db.ForeignKey("event.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    code=db.Column(db.String(160),unique=True,nullable=False)
    checked_in=db.Column(db.Boolean,default=False,nullable=False)
    issued_at=db.Column(db.DateTime(timezone=True),default=now)
    __table_args__=(db.UniqueConstraint("event_id","user_id",name="uq_event_ticket"),)

class Certificate(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    event_id=db.Column(db.Integer,db.ForeignKey("event.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    certificate_no=db.Column(db.String(160),unique=True,nullable=False)
    title=db.Column(db.String(255),nullable=False)
    issued_at=db.Column(db.DateTime(timezone=True),default=now)
    __table_args__=(db.UniqueConstraint("event_id","user_id",name="uq_event_certificate"),)

class StudentRequest(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"))
    request_type=db.Column(db.String(100),nullable=False)
    details=db.Column(db.Text,default="")
    status=db.Column(db.String(30),default="submitted",nullable=False)
    response=db.Column(db.Text,default="")
    tracking_no=db.Column(db.String(80),unique=True,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now)

class CampusService(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    kind=db.Column(db.String(50),nullable=False)
    name=db.Column(db.String(255),nullable=False)
    description=db.Column(db.Text,default="")
    location=db.Column(db.String(255),default="")
    contact=db.Column(db.String(255),default="")
    hours=db.Column(db.String(255),default="")
    status=db.Column(db.String(30),default="active")

class LostFoundItem(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    reporter_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    item_type=db.Column(db.String(30),default="lost")
    title=db.Column(db.String(255),nullable=False)
    description=db.Column(db.Text,default="")
    location=db.Column(db.String(255),default="")
    contact=db.Column(db.String(255),default="")
    status=db.Column(db.String(30),default="open")
    created_at=db.Column(db.DateTime(timezone=True),default=now)

class EmergencyContact(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(255),nullable=False)
    phone=db.Column(db.String(80),nullable=False)
    category=db.Column(db.String(80),default="emergency")
    location=db.Column(db.String(255),default="")

class BusRoute(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(255),nullable=False)
    stops=db.Column(db.Text,default="[]")
    departure_times=db.Column(db.Text,default="[]")
    active=db.Column(db.Boolean,default=True)

class HostelRoom(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    building=db.Column(db.String(120),nullable=False)
    room_no=db.Column(db.String(50),nullable=False)
    capacity=db.Column(db.Integer,default=1)
    status=db.Column(db.String(30),default="available")
    occupant_id=db.Column(db.Integer,db.ForeignKey("users.id"))

class LibraryItem(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    title=db.Column(db.String(255),nullable=False)
    author=db.Column(db.String(255),default="")
    isbn=db.Column(db.String(80),default="")
    category=db.Column(db.String(120),default="")
    copies=db.Column(db.Integer,default=1)
    available_copies=db.Column(db.Integer,default=1)

class LibraryLoan(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    item_id=db.Column(db.Integer,db.ForeignKey("library_item.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    borrowed_at=db.Column(db.DateTime(timezone=True),default=now)
    due_at=db.Column(db.DateTime(timezone=True))
    returned_at=db.Column(db.DateTime(timezone=True))

class CafeteriaItem(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(255),nullable=False)
    category=db.Column(db.String(100),default="")
    price=db.Column(db.Float,default=0)
    available=db.Column(db.Boolean,default=True)

class VerificationToken(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    token=db.Column(db.String(180),unique=True,nullable=False)
    purpose=db.Column(db.String(40),nullable=False)
    expires_at=db.Column(db.DateTime(timezone=True),nullable=False)
    used=db.Column(db.Boolean,default=False,nullable=False)

class PasswordResetToken(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    token=db.Column(db.String(180),unique=True,nullable=False)
    expires_at=db.Column(db.DateTime(timezone=True),nullable=False)
    used=db.Column(db.Boolean,default=False,nullable=False)

def row(x):
    return {c.name:getattr(x,c.name) for c in x.__table__.columns}

def notify(user_id,kind,title,body=""):
    db.session.add(Notification(user_id=user_id,kind=kind,title=title,body=body))

def membership(iid,uid):
    return InstitutionMembership.query.filter_by(institution_id=iid,user_id=uid,status="active").first()

def can_manage(iid,uid):
    m=membership(iid,uid)
    return bool(m and m.role in {"institution_owner","institution_admin","principal","dean","department_admin","teacher"})

def register(app):
    @app.post("/api/v1/auth/logout-all")
    @login_required
    def logout_all():
        AuthToken.query.filter_by(user_id=request.current_user.id,revoked=False).update({"revoked":True})
        db.session.commit()
        return jsonify(status="logged_out_all_devices")

    @app.post("/api/v1/auth/verification/request")
    @login_required
    def verification_request():
        t=VerificationToken(user_id=request.current_user.id,token=token_urlsafe(32),purpose="email",expires_at=now()+timedelta(hours=24))
        db.session.add(t);db.session.commit()
        return jsonify(status="created",token=t.token,expires_at=t.expires_at.isoformat())

    @app.post("/api/v1/auth/verification/confirm")
    def verification_confirm():
        d=request.get_json() or {}
        t=VerificationToken.query.filter_by(token=d.get("token"),purpose="email",used=False).first()
        if not t or utc_dt(t.expires_at)<now(): return jsonify(error="invalid_or_expired_token"),400
        p=db.session.get(UserProfile,t.user_id);p.is_verified=True if hasattr(p,"is_verified") else True
        t.used=True;db.session.commit();return jsonify(status="verified")

    @app.post("/api/v1/auth/password-reset/request")
    def password_reset_request():
        email=str((request.get_json() or {}).get("email","")).strip().lower()
        u=User.query.filter_by(email=email).first()
        if not u:return jsonify(status="accepted")
        t=PasswordResetToken(user_id=u.id,token=token_urlsafe(32),expires_at=now()+timedelta(hours=1))
        db.session.add(t);db.session.commit()
        return jsonify(status="accepted",token=t.token if app.config.get("EXPOSE_RESET_TOKEN",True) else None)

    @app.post("/api/v1/auth/password-reset/confirm")
    def password_reset_confirm():
        d=request.get_json() or {}
        t=PasswordResetToken.query.filter_by(token=d.get("token"),used=False).first()
        if not t or utc_dt(t.expires_at)<now():return jsonify(error="invalid_or_expired_token"),400
        password=d.get("password","")
        if len(password)<8:return jsonify(error="password_too_short"),400
        u=db.session.get(User,t.user_id);u.password_hash=generate_password_hash(password);t.used=True
        AuthToken.query.filter_by(user_id=u.id,revoked=False).update({"revoked":True})
        db.session.commit();return jsonify(status="password_changed")

    @app.get("/api/v1/teacher/dashboard")
    @login_required
    def teacher_dashboard():
        uid=request.current_user.id
        offerings=CourseOffering.query.filter_by(teacher_id=uid).all()
        oids=[x.id for x in offerings]
        students=Enrollment.query.filter(Enrollment.offering_id.in_(oids),Enrollment.status=="enrolled").count() if oids else 0
        assignments=Assignment.query.filter(Assignment.offering_id.in_(oids)).count() if oids else 0
        submissions=Submission.query.join(Assignment,Submission.assignment_id==Assignment.id).filter(Assignment.offering_id.in_(oids)).count() if oids else 0
        return jsonify(courses=[row(x) for x in offerings],stats={"courses":len(offerings),"students":students,"assignments":assignments,"submissions":submissions})

    @app.get("/api/v1/teacher/courses/<int:oid>/students")
    @login_required
    def teacher_students(oid):
        o=db.session.get(CourseOffering,oid)
        if not o or o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in Enrollment.query.filter_by(offering_id=oid,status="enrolled").all()])

    @app.get("/api/v1/teacher/assignments/<int:aid>/submissions")
    @login_required
    def teacher_submissions(aid):
        a=db.session.get(Assignment,aid);o=db.session.get(CourseOffering,a.offering_id) if a else None
        if not o or o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in Submission.query.filter_by(assignment_id=aid).order_by(Submission.submitted_at.desc()).all()])

    @app.get("/api/v1/teacher/attendance/<int:oid>")
    @login_required
    def teacher_attendance(oid):
        o=db.session.get(CourseOffering,oid)
        if not o or o.teacher_id!=request.current_user.id:return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in Attendance.query.filter_by(offering_id=oid).all()])

    @app.get("/api/v1/academic-calendar")
    @login_required
    def calendar():
        uid=request.current_user.id
        ms=InstitutionMembership.query.filter_by(user_id=uid,status="active").all()
        ids=[m.institution_id for m in ms]
        return jsonify(items=[row(x) for x in AcademicCalendarItem.query.filter(AcademicCalendarItem.institution_id.in_(ids)).order_by(AcademicCalendarItem.starts_at).all()] if ids else [])

    @app.post("/api/v1/institutions/<int:iid>/calendar")
    @login_required
    def add_calendar(iid):
        if not can_manage(iid,request.current_user.id):return jsonify(error="forbidden"),403
        d=request.get_json() or {}
        def dt(v):return datetime.fromisoformat(v.replace("Z","+00:00")) if v else None
        x=AcademicCalendarItem(institution_id=iid,department_id=d.get("department_id"),title=d.get("title",""),kind=d.get("kind","event"),starts_at=dt(d.get("starts_at")),ends_at=dt(d.get("ends_at")),description=d.get("description",""),location=d.get("location",""),audience=d.get("audience","all"))
        if not x.title:return jsonify(error="title_required"),400
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/groups/<int:gid>/feed")
    @login_required
    def group_feed(gid):
        if not GroupMembership.query.filter_by(group_id=gid,user_id=request.current_user.id,status="active").first():return jsonify(error="forbidden"),403
        posts=Post.query.filter_by(group_id=gid).order_by(Post.created_at.desc()).limit(100).all()
        out=[]
        for p in posts:
            comments=Comment.query.filter_by(post_id=p.id).order_by(Comment.created_at.asc()).all()
            reactions=Reaction.query.filter_by(post_id=p.id).all()
            poll=Poll.query.filter_by(post_id=p.id).first()
            item=row(p);item["comments"]=[row(c) for c in comments];item["reaction_count"]=len(reactions);item["my_reaction"]=next((r.reaction for r in reactions if r.user_id==request.current_user.id),None)
            if poll:
                item["poll"]={**row(poll),"options":[{**row(o),"votes":PollVote.query.filter_by(option_id=o.id).count()} for o in PollOption.query.filter_by(poll_id=poll.id).order_by(PollOption.position).all()]}
            out.append(item)
        return jsonify(items=out)

    @app.post("/api/v1/groups/<int:gid>/polls")
    @login_required
    def create_poll(gid):
        if not GroupMembership.query.filter_by(group_id=gid,user_id=request.current_user.id,status="active").first():return jsonify(error="forbidden"),403
        d=request.get_json() or {};q=str(d.get("question","")).strip();opts=[str(x).strip() for x in d.get("options",[]) if str(x).strip()]
        if not q or len(opts)<2:return jsonify(error="question_and_two_options_required"),400
        p=Post(group_id=gid,author_id=request.current_user.id,post_type="poll",body=q);db.session.add(p);db.session.flush()
        poll=Poll(post_id=p.id,question=q);db.session.add(poll);db.session.flush()
        for n,label in enumerate(opts):db.session.add(PollOption(poll_id=poll.id,label=label,position=n))
        db.session.commit();return jsonify(post_id=p.id),201

    @app.post("/api/v1/polls/<int:pid>/vote")
    @login_required
    def vote_poll(pid):
        p=db.session.get(Poll,pid)
        if not p:return jsonify(error="poll_not_found"),404
        if not GroupMembership.query.filter_by(group_id=db.session.get(Post,p.post_id).group_id,user_id=request.current_user.id,status="active").first():return jsonify(error="forbidden"),403
        oid=(request.get_json() or {}).get("option_id");opt=db.session.get(PollOption,oid)
        if not opt or opt.poll_id!=pid:return jsonify(error="option_not_found"),404
        PollVote.query.filter(PollVote.option_id.in_([x.id for x in PollOption.query.filter_by(poll_id=pid).all()]),PollVote.user_id==request.current_user.id).delete(synchronize_session=False)
        db.session.add(PollVote(option_id=oid,user_id=request.current_user.id));db.session.commit();return jsonify(status="voted")

    @app.post("/api/v1/posts/<int:pid>/attachments")
    @login_required
    def attach_post(pid):
        p=db.session.get(Post,pid)
        if not p or not GroupMembership.query.filter_by(group_id=p.group_id,user_id=request.current_user.id,status="active").first():return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=PostAttachment(post_id=pid,name=d.get("name","file"),url=d.get("url",""),mime_type=d.get("mime_type","application/octet-stream"))
        if not x.url:return jsonify(error="url_required"),400
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/search/all")
    @login_required
    def search_all():
        q=str(request.args.get("q","")).strip()
        if len(q)<2:return jsonify(items=[])
        like="%"+q+"%"
        memberships=InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()
        ids=[m.institution_id for m in memberships]
        if not ids:return jsonify(items=[])
        dep_ids=[d.id for d in Department.query.filter(Department.institution_id.in_(ids)).all()]
        items=[]
        user_ids=[m.user_id for m in InstitutionMembership.query.filter(InstitutionMembership.institution_id.in_(ids),InstitutionMembership.status=="active").all()]
        if user_ids:
            for x in UserProfile.query.filter(UserProfile.user_id.in_(user_ids),((UserProfile.full_name.ilike(like))|(UserProfile.username.ilike(like)))).limit(20):
                items.append({"type":"student_or_user","id":x.user_id,"title":x.full_name,"subtitle":x.username})
        for x in Course.query.filter(Course.department_id.in_(dep_ids),((Course.title.ilike(like))|(Course.code.ilike(like)))).limit(20) if dep_ids else []:
            items.append({"type":"course","id":x.id,"title":x.title,"subtitle":x.code})
        for x in Department.query.filter(Department.id.in_(dep_ids),((Department.name.ilike(like))|(Department.code.ilike(like)))).limit(20) if dep_ids else []:
            items.append({"type":"department","id":x.id,"title":x.name,"subtitle":x.code})
        for x in Institution.query.filter(Institution.id.in_(ids),Institution.name.ilike(like)).limit(20):
            items.append({"type":"institution","id":x.id,"title":x.name,"subtitle":x.slug})
        return jsonify(items=items[:80])

    @app.get("/api/v1/events/<int:eid>/ticket")
    @login_required
    def event_ticket(eid):
        t=EventTicket.query.filter_by(event_id=eid,user_id=request.current_user.id).first()
        if not t:
            t=EventTicket(event_id=eid,user_id=request.current_user.id,code=token_urlsafe(24));db.session.add(t);db.session.commit()
        return jsonify(data=row(t))

    @app.post("/api/v1/events/tickets/<code>/check-in")
    @login_required
    def checkin(code):
        t=EventTicket.query.filter_by(code=code).first()
        if not t:return jsonify(error="ticket_not_found"),404
        e=db.session.get(Event,t.event_id)
        if not e or not can_manage(e.institution_id,request.current_user.id):return jsonify(error="forbidden"),403
        t.checked_in=True;db.session.commit();return jsonify(status="checked_in",ticket=row(t))

    @app.post("/api/v1/events/<int:eid>/certificate")
    @login_required
    def issue_certificate(eid):
        e=db.session.get(Event,eid)
        if not e or not can_manage(e.institution_id,request.current_user.id):return jsonify(error="forbidden"),403
        uid=(request.get_json() or {}).get("user_id")
        if not uid:return jsonify(error="user_id_required"),400
        c=Certificate.query.filter_by(event_id=eid,user_id=uid).first()
        if not c:
            c=Certificate(event_id=eid,user_id=uid,certificate_no="CERT-"+token_urlsafe(10),title=e.title);db.session.add(c);db.session.commit()
        return jsonify(data=row(c))

    @app.get("/api/v1/certificates")
    @login_required
    def certificates():
        return jsonify(items=[row(x) for x in Certificate.query.filter_by(user_id=request.current_user.id).order_by(Certificate.issued_at.desc()).all()])

    @app.post("/api/v1/service-requests/advanced")
    @login_required
    def advanced_request():
        d=request.get_json() or {};iid=d.get("institution_id")
        x=StudentRequest(user_id=request.current_user.id,institution_id=iid,request_type=d.get("request_type","general"),details=d.get("details",""),tracking_no="REQ-"+token_urlsafe(8))
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/service-requests/advanced")
    @login_required
    def my_advanced_requests():
        return jsonify(items=[row(x) for x in StudentRequest.query.filter_by(user_id=request.current_user.id).order_by(StudentRequest.created_at.desc()).all()])

    @app.get("/api/v1/campus-services")
    @login_required
    def campus_services():
        ms=InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all();ids=[m.institution_id for m in ms]
        return jsonify(items=[row(x) for x in CampusService.query.filter(CampusService.institution_id.in_(ids)).all()] if ids else [])

    @app.post("/api/v1/institutions/<int:iid>/campus-services")
    @login_required
    def add_campus_service(iid):
        if not can_manage(iid,request.current_user.id):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=CampusService(institution_id=iid,kind=d.get("kind","general"),name=d.get("name",""),description=d.get("description",""),location=d.get("location",""),contact=d.get("contact",""),hours=d.get("hours",""))
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/lost-found")
    @login_required
    def lost_found():
        ms=InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all();ids=[m.institution_id for m in ms]
        return jsonify(items=[row(x) for x in LostFoundItem.query.filter(LostFoundItem.institution_id.in_(ids)).order_by(LostFoundItem.created_at.desc()).all()] if ids else [])

    @app.post("/api/v1/institutions/<int:iid>/lost-found")
    @login_required
    def create_lost_found(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="membership_required"),403
        d=request.get_json() or {};x=LostFoundItem(institution_id=iid,reporter_id=request.current_user.id,item_type=d.get("item_type","lost"),title=d.get("title",""),description=d.get("description",""),location=d.get("location",""),contact=d.get("contact",""))
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/emergency-contacts/<int:iid>")
    @login_required
    def emergency_contacts(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in EmergencyContact.query.filter_by(institution_id=iid).all()])

    @app.get("/api/v1/bus-routes/<int:iid>")
    @login_required
    def bus_routes(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in BusRoute.query.filter_by(institution_id=iid,active=True).all()])

    @app.get("/api/v1/hostel/<int:iid>/rooms")
    @login_required
    def hostel_rooms(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in HostelRoom.query.filter_by(institution_id=iid).all()])

    @app.post("/api/v1/hostel/<int:iid>/apply")
    @login_required
    def hostel_apply(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=StudentRequest(user_id=request.current_user.id,institution_id=iid,request_type="hostel",details=str(d.get("details","")),tracking_no="HOSTEL-"+token_urlsafe(8));db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/library/<int:iid>/items")
    @login_required
    def library_items(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in LibraryItem.query.filter_by(institution_id=iid).all()])

    @app.get("/api/v1/library/my-loans")
    @login_required
    def my_library_loans():
        return jsonify(items=[row(x) for x in LibraryLoan.query.filter_by(user_id=request.current_user.id).order_by(LibraryLoan.borrowed_at.desc()).all()])

    @app.post("/api/v1/library/items/<int:item_id>/borrow")
    @login_required
    def borrow_library(item_id):
        x=db.session.get(LibraryItem,item_id)
        if not x or x.available_copies<1:return jsonify(error="not_available"),409
        if LibraryLoan.query.filter_by(item_id=item_id,user_id=request.current_user.id,returned_at=None).first():return jsonify(error="already_borrowed"),409
        loan=LibraryLoan(item_id=item_id,user_id=request.current_user.id,due_at=now()+timedelta(days=14));x.available_copies-=1;db.session.add(loan);db.session.commit();return jsonify(data=row(loan)),201

    @app.post("/api/v1/library/loans/<int:lid>/return")
    @login_required
    def return_library(lid):
        x=db.session.get(LibraryLoan,lid)
        if not x or x.user_id!=request.current_user.id or x.returned_at:return jsonify(error="loan_not_found"),404
        x.returned_at=now();item=db.session.get(LibraryItem,x.item_id);item.available_copies+=1;db.session.commit();return jsonify(status="returned")

    @app.get("/api/v1/cafeteria/<int:iid>")
    @login_required
    def cafeteria(iid):
        if not membership(iid,request.current_user.id):return jsonify(error="forbidden"),403
        return jsonify(items=[row(x) for x in CafeteriaItem.query.filter_by(institution_id=iid,available=True).all()])

    @app.get("/api/v1/results/semester/<int:semester_id>")
    @login_required
    def semester_results(semester_id):
        return jsonify(items=[row(x) for x in Result.query.filter_by(student_id=request.current_user.id,semester_id=semester_id,published=True).all()])

    @app.get("/api/v1/transcript.pdf")
    @login_required
    def transcript_pdf():
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        buf=BytesIO();pdf=canvas.Canvas(buf,pagesize=A4);w,h=A4
        p=request.current_user.profile;pdf.setTitle("CampusHub Official Transcript")
        pdf.setFont("Helvetica-Bold",18);pdf.drawString(50,h-55,"CampusHub — Official Transcript")
        pdf.setFont("Helvetica",10);pdf.drawString(50,h-78,"Student: "+p.full_name);pdf.drawString(50,h-94,"Student ID: "+str(p.student_id or ""));pdf.drawString(50,h-110,"Program: "+str(p.program or ""))
        rows=Result.query.filter_by(student_id=request.current_user.id,published=True).all();y=h-145
        pdf.setFont("Helvetica-Bold",10);pdf.drawString(50,y,"Course");pdf.drawString(300,y,"Grade");pdf.drawString(380,y,"Point");pdf.drawString(450,y,"Credits");y-=18;pdf.setFont("Helvetica",9)
        credits=points=0
        for r in rows:
            c=db.session.get(Course,r.course_id);pdf.drawString(50,y,(c.code+" — "+c.title)[:42] if c else str(r.course_id));pdf.drawString(300,y,r.grade);pdf.drawString(380,y,f"{r.grade_point:.2f}");pdf.drawString(450,y,f"{r.credits:.1f}");credits+=r.credits;points+=r.credits*r.grade_point;y-=15
            if y<55:pdf.showPage();y=h-55
        cgpa=points/credits if credits else 0
        pdf.setFont("Helvetica-Bold",11);pdf.drawString(50,y-10,f"CGPA: {cgpa:.2f}   Total Credits: {credits:.1f}")
        pdf.save();buf.seek(0);return send_file(buf,mimetype="application/pdf",as_attachment=True,download_name="campushub-transcript.pdf")
