from datetime import datetime,timezone
from flask import request,jsonify
from backend.core import db,UserProfile,Institution,Group
from backend.api import login_required
class Message(db.Model):
    id=db.Column(db.Integer,primary_key=True);sender_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);recipient_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);body=db.Column(db.Text,nullable=False);read_at=db.Column(db.DateTime(timezone=True));created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
def data(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def register(app):
    @app.patch("/api/v1/profile")
    @login_required
    def profile():
        p=request.current_user.profile;d=request.get_json() or {}
        for k in ("full_name","phone","address","bio","profile_photo_url","institution_text","department","program","student_id"):
            if k in d:setattr(p,k,d[k])
        db.session.commit();return jsonify(profile={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ("id","user_id")})
    @app.get("/api/v1/messages")
    @login_required
    def messages():return jsonify(items=[data(x) for x in Message.query.filter((Message.sender_id==request.current_user.id)|(Message.recipient_id==request.current_user.id)).order_by(Message.created_at.desc()).limit(100).all()])
    @app.post("/api/v1/messages")
    @login_required
    def send():
        d=request.get_json() or {};recipient_id=d.get("recipient_id");body=str(d.get("body","")).strip()
        if not recipient_id or not body:return jsonify(error="recipient_and_body_required"),400
        if int(recipient_id)==request.current_user.id:return jsonify(error="cannot_message_self"),400
        from backend.core import User,Notification
        recipient=db.session.get(User,int(recipient_id))
        if not recipient:return jsonify(error="recipient_not_found"),404
        x=Message(sender_id=request.current_user.id,recipient_id=recipient.id,body=body);db.session.add(x)
        db.session.add(Notification(user_id=recipient.id,kind="message",title="New message",body=f"You have a new message from user #{request.current_user.id}."))
        db.session.commit();return jsonify(data(x)),201

    @app.post("/api/v1/messages/<int:mid>/read")
    @login_required
    def read_message(mid):
        x=db.session.get(Message,mid)
        if not x or x.recipient_id!=request.current_user.id:return jsonify(error="message_not_found"),404
        x.read_at=datetime.now(timezone.utc);db.session.commit();return jsonify(data(x))

    @app.get("/api/v1/profile")
    @login_required
    def get_profile():
        p=request.current_user.profile
        return jsonify(profile={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ("id","user_id")})
    @app.get("/api/v1/search")
    @login_required
    def search():
        q=request.args.get("q","").strip();like=f"%{q}%";out=[]
        out += [{"type":"institution","id":x.id,"title":x.name} for x in Institution.query.filter(Institution.name.ilike(like)).limit(10)]
        out += [{"type":"user","id":x.user_id,"title":x.full_name} for x in UserProfile.query.filter(UserProfile.full_name.ilike(like)).limit(20)]
        out += [{"type":"group","id":x.id,"title":x.name} for x in Group.query.filter(Group.name.ilike(like)).limit(20)]
        return jsonify(items=out)

from backend.academic import Enrollment, Assignment, Attendance
def register_dashboard(app):
    @app.get("/api/v1/dashboard")
    @login_required
    def dashboard():
        uid=request.current_user.id
        enrollments=Enrollment.query.filter_by(student_id=uid,status="enrolled").all()
        ids=[x.offering_id for x in enrollments]
        assignments=Assignment.query.filter(Assignment.offering_id.in_(ids)).limit(10).all() if ids else []
        att=Attendance.query.filter_by(student_id=uid).all()
        present=sum(x.status=="present" for x in att)
        from backend.core import Notification
        unread=Notification.query.filter_by(user_id=uid,is_read=False).count()
        return jsonify(stats={"courses":len(enrollments),"upcoming_assignments":len(assignments),"attendance_percent":round(present/len(att)*100,1) if att else 0,"unread_notifications":unread},assignments=[{k:getattr(x,k) for k in ("id","title","description","due_at","max_score")} for x in assignments])
