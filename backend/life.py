from datetime import datetime, timezone
from flask import request, jsonify
from backend.core import db,InstitutionMembership
from backend.api import login_required
class Event(db.Model):
    id=db.Column(db.Integer,primary_key=True);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"));organizer_id=db.Column(db.Integer,db.ForeignKey("users.id"));title=db.Column(db.String(255),nullable=False);description=db.Column(db.Text,default="");starts_at=db.Column(db.DateTime(timezone=True));ends_at=db.Column(db.DateTime(timezone=True));location=db.Column(db.String(255),default="");event_type=db.Column(db.String(60),default="event");capacity=db.Column(db.Integer);created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class EventRegistration(db.Model):
    id=db.Column(db.Integer,primary_key=True);event_id=db.Column(db.Integer,db.ForeignKey("event.id"),nullable=False);user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);registered_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    __table_args__=(db.UniqueConstraint("event_id","user_id",name="uq_event_user"),)
class Club(db.Model):
    id=db.Column(db.Integer,primary_key=True);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"),nullable=False);name=db.Column(db.String(255),nullable=False);description=db.Column(db.Text,default="");logo_url=db.Column(db.String(500),default="")
class ClubMembership(db.Model):
    id=db.Column(db.Integer,primary_key=True);club_id=db.Column(db.Integer,db.ForeignKey("club.id"),nullable=False);user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);role=db.Column(db.String(40),default="member")
    __table_args__=(db.UniqueConstraint("club_id","user_id",name="uq_club_user"),)
class Document(db.Model):
    id=db.Column(db.Integer,primary_key=True);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"));owner_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);title=db.Column(db.String(255),nullable=False);category=db.Column(db.String(80),default="general");url=db.Column(db.String(500),nullable=False);created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class ServiceRequest(db.Model):
    id=db.Column(db.Integer,primary_key=True);user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"));request_type=db.Column(db.String(100),nullable=False);details=db.Column(db.Text,default="");status=db.Column(db.String(30),default="submitted");response=db.Column(db.Text,default="");created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Fee(db.Model):
    id=db.Column(db.Integer,primary_key=True);student_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"));title=db.Column(db.String(255),nullable=False);amount=db.Column(db.Float,default=0);due_date=db.Column(db.Date);status=db.Column(db.String(30),default="unpaid")
def data(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def register(app):
    @app.get("/api/v1/events")
    @login_required
    def events():
        ids=[m.institution_id for m in InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()]
        return jsonify(items=[data(x) for x in Event.query.filter(Event.institution_id.in_(ids)).order_by(Event.starts_at.asc()).limit(100).all()] if ids else [])
    @app.post("/api/v1/events")
    @login_required
    def add_event():
        d=request.get_json() or {};iid=d.get("institution_id")
        if not iid or not InstitutionMembership.query.filter_by(institution_id=iid,user_id=request.current_user.id,status="active").first():return jsonify(error="membership_required"),403
        x=Event(institution_id=iid,organizer_id=request.current_user.id,title=d.get("title",""),description=d.get("description",""),starts_at=datetime.fromisoformat(d["starts_at"].replace("Z","+00:00")) if d.get("starts_at") else None,ends_at=datetime.fromisoformat(d["ends_at"].replace("Z","+00:00")) if d.get("ends_at") else None,location=d.get("location",""),event_type=d.get("event_type","event"))
        if not x.title.strip():return jsonify(error="title_required"),400
        db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.post("/api/v1/events/<int:eid>/register")
    @login_required
    def register_event(eid):
        e=db.get_or_404(Event,eid)
        if not InstitutionMembership.query.filter_by(institution_id=e.institution_id,user_id=request.current_user.id,status="active").first():return jsonify(error="membership_required"),403
        if e.capacity and EventRegistration.query.filter_by(event_id=eid).count()>=e.capacity:return jsonify(error="event_full"),409
        if EventRegistration.query.filter_by(event_id=eid,user_id=request.current_user.id).first():return jsonify(error="already_registered"),409
        x=EventRegistration(event_id=eid,user_id=request.current_user.id);db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/clubs")
    @login_required
    def clubs():
        ids=[m.institution_id for m in InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()]
        return jsonify(items=[data(x) for x in Club.query.filter(Club.institution_id.in_(ids)).order_by(Club.name).all()] if ids else [])
    @app.post("/api/v1/clubs")
    @login_required
    def add_club():
        d=request.get_json() or {};iid=d.get("institution_id")
        if not iid or not InstitutionMembership.query.filter_by(institution_id=iid,user_id=request.current_user.id,status="active").first():return jsonify(error="membership_required"),403
        x=Club(institution_id=iid,name=d.get("name",""),description=d.get("description",""),logo_url=d.get("logo_url",""))
        if not x.name.strip():return jsonify(error="name_required"),400
        db.session.add(x);db.session.flush();db.session.add(ClubMembership(club_id=x.id,user_id=request.current_user.id,role="admin"));db.session.commit();return jsonify(data(x)),201
    @app.post("/api/v1/clubs/<int:cid>/join")
    @login_required
    def join_club(cid):
        club=db.get_or_404(Club,cid)
        if not InstitutionMembership.query.filter_by(institution_id=club.institution_id,user_id=request.current_user.id,status="active").first():return jsonify(error="membership_required"),403
        if ClubMembership.query.filter_by(club_id=cid,user_id=request.current_user.id).first():return jsonify(error="already_member"),409
        x=ClubMembership(club_id=cid,user_id=request.current_user.id);db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/documents")
    @login_required
    def documents():
        ids=[m.institution_id for m in InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()]
        return jsonify(items=[data(x) for x in Document.query.filter(Document.institution_id.in_(ids)).order_by(Document.created_at.desc()).all()] if ids else [])
    @app.post("/api/v1/documents")
    @login_required
    def add_document():
        d=request.get_json() or {};iid=d.get("institution_id")
        if not iid or not InstitutionMembership.query.filter_by(institution_id=iid,user_id=request.current_user.id,status="active").first():return jsonify(error="membership_required"),403
        x=Document(institution_id=iid,owner_id=request.current_user.id,title=d.get("title",""),category=d.get("category","general"),url=d.get("url",""))
        if not x.title.strip() or not x.url.strip():return jsonify(error="title_and_url_required"),400
        db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/service-requests")
    @login_required
    def services():return jsonify(items=[data(x) for x in ServiceRequest.query.filter_by(user_id=request.current_user.id).all()])
    @app.post("/api/v1/service-requests")
    @login_required
    def add_service():
        d=request.get_json() or {};iid=d.get("institution_id")
        if iid and not InstitutionMembership.query.filter_by(institution_id=iid,user_id=request.current_user.id,status="active").first():return jsonify(error="membership_required"),403
        x=ServiceRequest(user_id=request.current_user.id,institution_id=iid,request_type=str(d.get("request_type","general")).strip(),details=d.get("details",""))
        if not x.request_type:return jsonify(error="request_type_required"),400
        db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/fees")
    @login_required
    def fees():return jsonify(items=[data(x) for x in Fee.query.filter_by(student_id=request.current_user.id).all()])
    @app.get("/api/v1/fees/<int:fid>")
    @login_required
    def fee_detail(fid):
        f=db.get_or_404(Fee,fid)
        if f.student_id!=request.current_user.id:return jsonify(error="forbidden"),403
        return jsonify(data(f))
