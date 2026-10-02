from datetime import datetime,timezone
from flask import request,jsonify
from werkzeug.security import check_password_hash,generate_password_hash
from backend.core import db,Notification,InstitutionMembership,JoinRequest,Institution
from backend.api import login_required,institution_manager

class Announcement(db.Model):
    id=db.Column(db.Integer,primary_key=True);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"),nullable=False);author_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);title=db.Column(db.String(255),nullable=False);body=db.Column(db.Text,nullable=False);audience=db.Column(db.String(50),default="all");created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

def data(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def register(app):
    @app.get("/api/v1/notifications")
    @login_required
    def platform_notifications():return jsonify(items=[data(x) for x in Notification.query.filter_by(user_id=request.current_user.id).order_by(Notification.created_at.desc()).limit(100).all()])
    @app.post("/api/v1/notifications/<int:nid>/read")
    @login_required
    def notification_read(nid):
        x=db.get_or_404(Notification,nid)
        if x.user_id!=request.current_user.id:return jsonify(error="forbidden"),403
        x.is_read=True;db.session.commit();return jsonify(status="read")
    @app.post("/api/v1/auth/change-password")
    @login_required
    def change_password():
        d=request.get_json() or {}
        if not check_password_hash(request.current_user.password_hash,d.get("current_password","")):return jsonify(error="invalid_current_password"),400
        if len(d.get("new_password",""))<8:return jsonify(error="password_too_short"),400
        request.current_user.password_hash=generate_password_hash(d["new_password"]);db.session.commit();return jsonify(status="changed")
    @app.get("/api/v1/institutions/<int:iid>/stats")
    @login_required
    def stats(iid):
        if not institution_manager(iid):return jsonify(error="forbidden"),403
        return jsonify(members=InstitutionMembership.query.filter_by(institution_id=iid,status="active").count(),pending_requests=JoinRequest.query.filter_by(institution_id=iid,status="pending").count())
    @app.get("/api/v1/institutions/<int:iid>/announcements")
    def announcements(iid):return jsonify(items=[data(x) for x in Announcement.query.filter_by(institution_id=iid).order_by(Announcement.created_at.desc()).all()])
    @app.post("/api/v1/institutions/<int:iid>/announcements")
    @login_required
    def add_announcement(iid):
        if not institution_manager(iid):return jsonify(error="forbidden"),403
        d=request.get_json() or {};x=Announcement(institution_id=iid,author_id=request.current_user.id,title=d.get("title",""),body=d.get("body",""),audience=d.get("audience","all"));db.session.add(x)
        members=InstitutionMembership.query.filter_by(institution_id=iid,status="active").all()
        for m in members:db.session.add(Notification(user_id=m.user_id,kind="announcement",title=x.title,body=x.body))
        db.session.commit();return jsonify(data(x)),201
