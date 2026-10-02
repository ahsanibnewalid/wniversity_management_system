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
        d=request.get_json() or {};x=Message(sender_id=request.current_user.id,recipient_id=d["recipient_id"],body=d.get("body",""));db.session.add(x);db.session.commit();return jsonify(data(x)),201
    @app.get("/api/v1/search")
    @login_required
    def search():
        q=request.args.get("q","").strip();like=f"%{q}%";out=[]
        out += [{"type":"institution","id":x.id,"title":x.name} for x in Institution.query.filter(Institution.name.ilike(like)).limit(10)]
        out += [{"type":"user","id":x.user_id,"title":x.full_name} for x in UserProfile.query.filter(UserProfile.full_name.ilike(like)).limit(20)]
        out += [{"type":"group","id":x.id,"title":x.name} for x in Group.query.filter(Group.name.ilike(like)).limit(20)]
        return jsonify(items=out)
