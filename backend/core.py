import os
from datetime import datetime, timezone
from secrets import token_urlsafe
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

db=SQLAlchemy()
TOKENS={}
def now(): return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(255),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)
    profile=db.relationship("UserProfile",backref="user",uselist=False,cascade="all, delete-orphan")

class UserProfile(db.Model):
    __tablename__="user_profiles"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),unique=True,nullable=False)
    full_name=db.Column(db.String(160),nullable=False)
    username=db.Column(db.String(80),unique=True,nullable=False)
    phone=db.Column(db.String(40)); address=db.Column(db.String(255)); bio=db.Column(db.Text)
    profile_photo_url=db.Column(db.String(500)); institution_text=db.Column(db.String(200))
    department=db.Column(db.String(160)); program=db.Column(db.String(160)); student_id=db.Column(db.String(100))
    is_complete=db.Column(db.Boolean,default=False,nullable=False)


class AuthToken(db.Model):
    __tablename__="auth_tokens"
    id=db.Column(db.Integer,primary_key=True)
    token=db.Column(db.String(128),unique=True,nullable=False,index=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)
    revoked=db.Column(db.Boolean,default=False,nullable=False)

class Institution(db.Model):
    __tablename__="institutions"
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(200),unique=True,nullable=False)
    slug=db.Column(db.String(120),unique=True,nullable=False); kind=db.Column(db.String(80),default="university",nullable=False)
    address=db.Column(db.String(255)); website=db.Column(db.String(500)); description=db.Column(db.Text)
    owner_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)

class InstitutionMembership(db.Model):
    __tablename__="institution_memberships"
    id=db.Column(db.Integer,primary_key=True); institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    role=db.Column(db.String(50),default="student",nullable=False); status=db.Column(db.String(30),default="active",nullable=False)
    student_id=db.Column(db.String(100)); program=db.Column(db.String(160))
    __table_args__=(db.UniqueConstraint("institution_id","user_id",name="uq_institution_user"),)

class Department(db.Model):
    __tablename__="departments"
    id=db.Column(db.Integer,primary_key=True); institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(160),nullable=False); code=db.Column(db.String(40),nullable=False)
    __table_args__=(db.UniqueConstraint("institution_id","name",name="uq_department_name"),)

class AcademicSession(db.Model):
    __tablename__="academic_sessions"
    id=db.Column(db.Integer,primary_key=True); department_id=db.Column(db.Integer,db.ForeignKey("departments.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(80),nullable=False)
    __table_args__=(db.UniqueConstraint("department_id","name",name="uq_session_name"),)

class AcademicYear(db.Model):
    __tablename__="academic_years"
    id=db.Column(db.Integer,primary_key=True); session_id=db.Column(db.Integer,db.ForeignKey("academic_sessions.id",ondelete="CASCADE"),nullable=False)
    name=db.Column(db.String(80),nullable=False)
    __table_args__=(db.UniqueConstraint("session_id","name",name="uq_year_name"),)

class Group(db.Model):
    __tablename__="groups"
    id=db.Column(db.Integer,primary_key=True); institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    department_id=db.Column(db.Integer,db.ForeignKey("departments.id",ondelete="CASCADE")); session_id=db.Column(db.Integer,db.ForeignKey("academic_sessions.id",ondelete="CASCADE"))
    academic_year_id=db.Column(db.Integer,db.ForeignKey("academic_years.id",ondelete="CASCADE")); name=db.Column(db.String(180),nullable=False)
    group_type=db.Column(db.String(40),nullable=False); description=db.Column(db.Text); is_private=db.Column(db.Boolean,default=False,nullable=False)

class GroupMembership(db.Model):
    __tablename__="group_memberships"
    id=db.Column(db.Integer,primary_key=True); group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False); role=db.Column(db.String(50),default="member",nullable=False)
    status=db.Column(db.String(30),default="active",nullable=False)
    __table_args__=(db.UniqueConstraint("group_id","user_id",name="uq_group_user"),)

class JoinRequest(db.Model):
    __tablename__="join_requests"
    id=db.Column(db.Integer,primary_key=True); institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False); department_id=db.Column(db.Integer,db.ForeignKey("departments.id"))
    student_id=db.Column(db.String(100),nullable=False); program=db.Column(db.String(160),nullable=False); session=db.Column(db.String(80),nullable=False)
    academic_year=db.Column(db.String(80),nullable=False); note=db.Column(db.Text); status=db.Column(db.String(30),default="pending",nullable=False)
    reviewed_by=db.Column(db.Integer,db.ForeignKey("users.id")); created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)

class Post(db.Model):
    __tablename__="posts"
    id=db.Column(db.Integer,primary_key=True); group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False); post_type=db.Column(db.String(30),default="post",nullable=False)
    body=db.Column(db.Text,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)

class Comment(db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True); post_id=db.Column(db.Integer,db.ForeignKey("posts.id",ondelete="CASCADE"),nullable=False)
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False); body=db.Column(db.Text,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)

class Reaction(db.Model):
    __tablename__="reactions"
    id=db.Column(db.Integer,primary_key=True); post_id=db.Column(db.Integer,db.ForeignKey("posts.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False); reaction=db.Column(db.String(30),default="like",nullable=False)
    __table_args__=(db.UniqueConstraint("post_id","user_id",name="uq_post_user_reaction"),)

class Notification(db.Model):
    __tablename__="notifications"
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    kind=db.Column(db.String(60),nullable=False); title=db.Column(db.String(200),nullable=False); body=db.Column(db.Text)
    is_read=db.Column(db.Boolean,default=False,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)

MANAGERS={"institution_owner","institution_admin","principal"}

def create_app():
    app=Flask(__name__)
    uri=os.getenv("DATABASE_URL","sqlite:///campushub.db")
    if uri.startswith("postgres://"): uri=uri.replace("postgres://","postgresql+psycopg://",1)
    elif uri.startswith("postgresql://") and "+psycopg" not in uri: uri=uri.replace("postgresql://","postgresql+psycopg://",1)
    app.config.update(SECRET_KEY=os.getenv("SECRET_KEY","dev-change-me"),SQLALCHEMY_DATABASE_URI=uri,SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app); CORS(app,resources={r"/api/*":{"origins":os.getenv("CORS_ORIGINS","*")}})
    with app.app_context(): db.create_all()
    def user():
        h=request.headers.get("Authorization",""); t=h[7:] if h.startswith("Bearer ") else ""; row=AuthToken.query.filter_by(token=t,revoked=False).first()
        return db.session.get(User,row.user_id) if row else None
    def auth():
        u=user()
        return (u,None) if u else (None,({"error":"authentication_required"},401))
    @app.get("/healthz")
    def healthz():
        try: db.session.execute(db.text("SELECT 1")); return {"status":"ok","database":"ok"}
        except Exception: return {"status":"error","database":"unavailable"},503
    @app.post("/api/v1/auth/register")
    def register():
        d=request.get_json(silent=True) or {}; email=d.get("email","").strip().lower(); password=d.get("password",""); name=d.get("full_name","").strip(); username=d.get("username","").strip().lower()
        if not all((email,password,name,username)): return {"error":"email,password,full_name,username_required"},400
        if User.query.filter_by(email=email).first() or UserProfile.query.filter_by(username=username).first(): return {"error":"email_or_username_exists"},409
        u=User(email=email,password_hash=generate_password_hash(password)); db.session.add(u); db.session.flush(); db.session.add(UserProfile(user_id=u.id,full_name=name,username=username,is_complete=False)); db.session.commit()
        return {"user_id":u.id,"profile_complete":False},201
    @app.post("/api/v1/auth/login")
    def login():
        d=request.get_json(silent=True) or {}; u=User.query.filter_by(email=d.get("email","").strip().lower()).first()
        if not u or not check_password_hash(u.password_hash,d.get("password","")): return {"error":"invalid_credentials"},401
         t=AuthToken(token=token_urlsafe(48),user_id=u.id); db.session.add(t); db.session.commit(); return {"access_token":t.token,"token_type":"Bearer","user_id":u.id,"profile_complete":u.profile.is_complete}
    @app.get("/api/v1/auth/me")
    def me():
        u,e=auth()
        if e:return e
        return {"id":u.id,"email":u.email,"profile":{"full_name":u.profile.full_name,"username":u.profile.username,"is_complete":u.profile.is_complete}}
    @app.get("/api/v1/institutions")
    def institutions():
        return {"items":[{"id":i.id,"name":i.name,"slug":i.slug,"kind":i.kind,"address":i.address} for i in Institution.query.order_by(Institution.name).all()]}
    @app.post("/api/v1/institutions")
    def create_institution():
        u,e=auth()
        if e:return e
        d=request.get_json(silent=True) or {}
        if not u.profile.is_complete:return {"error":"complete_profile_first"},403
        if not d.get("name") or not d.get("slug"):return {"error":"name_and_slug_required"},400
        i=Institution(name=d["name"].strip(),slug=d["slug"].strip().lower(),kind=d.get("kind","university"),address=d.get("address"),website=d.get("website"),description=d.get("description"),owner_id=u.id)
        db.session.add(i); db.session.flush(); db.session.add(InstitutionMembership(institution_id=i.id,user_id=u.id,role="institution_owner")); db.session.commit()
        return {"id":i.id,"slug":i.slug},201
    @app.post("/api/v1/institutions/<int:iid>/join")
    def join(iid):
        u,e=auth()
        if e:return e
        if not u.profile.is_complete:return {"error":"complete_profile_first"},403
        d=request.get_json(silent=True) or {}; required=("department_id","student_id","program","session","academic_year")
        if not all(d.get(k) for k in required):return {"error":"academic_details_required"},400
        if JoinRequest.query.filter_by(institution_id=iid,user_id=u.id,status="pending").first():return {"error":"request_pending"},409
        r=JoinRequest(institution_id=iid,user_id=u.id,department_id=d["department_id"],student_id=d["student_id"],program=d["program"],session=d["session"],academic_year=d["academic_year"],note=d.get("note"))
        db.session.add(r); db.session.commit(); return {"request_id":r.id,"status":"pending"},201
    @app.get("/api/v1/institutions/<int:iid>/groups")
    def institution_groups(iid):
        gs=Group.query.filter_by(institution_id=iid).order_by(Group.name).all()
        return {"items":[{"id":g.id,"name":g.name,"type":g.group_type,"department_id":g.department_id,"session_id":g.session_id,"academic_year_id":g.academic_year_id} for g in gs]}
    @app.post("/api/v1/groups")
    def create_group():
        u,e=auth()
        if e:return e
        d=request.get_json(silent=True) or {}; m=InstitutionMembership.query.filter_by(institution_id=d.get("institution_id"),user_id=u.id,status="active").first()
        if not m or m.role not in MANAGERS:return {"error":"forbidden"},403
        g=Group(institution_id=d["institution_id"],department_id=d.get("department_id"),session_id=d.get("session_id"),academic_year_id=d.get("academic_year_id"),name=d["name"],group_type=d["group_type"],description=d.get("description"),is_private=bool(d.get("is_private",False)))
        db.session.add(g); db.session.commit(); return {"id":g.id},201
    @app.post("/api/v1/groups/<int:gid>/join")
    def join_group(gid):
        u,e=auth()
        if e:return e
        g=db.session.get(Group,gid)
        if not g:return {"error":"group_not_found"},404
        if not InstitutionMembership.query.filter_by(institution_id=g.institution_id,user_id=u.id,status="active").first():return {"error":"institution_membership_required"},403
        if not GroupMembership.query.filter_by(group_id=gid,user_id=u.id).first():db.session.add(GroupMembership(group_id=gid,user_id=u.id));db.session.commit()
        return {"status":"active"}
    @app.get("/api/v1/groups/<int:gid>/posts")
    def posts(gid):
        ps=Post.query.filter_by(group_id=gid).order_by(Post.created_at.desc()).limit(50).all()
        return {"items":[{"id":p.id,"author_id":p.author_id,"type":p.post_type,"body":p.body,"created_at":p.created_at.isoformat()} for p in ps]}
    @app.post("/api/v1/groups/<int:gid>/posts")
    def create_post(gid):
        u,e=auth()
        if e:return e
        if not GroupMembership.query.filter_by(group_id=gid,user_id=u.id,status="active").first():return {"error":"group_membership_required"},403
        d=request.get_json(silent=True) or {}; body=d.get("body","").strip()
        if not body:return {"error":"body_required"},400
        p=Post(group_id=gid,author_id=u.id,post_type=d.get("post_type","post"),body=body);db.session.add(p);db.session.commit();return {"id":p.id},201
    @app.post("/api/v1/posts/<int:pid>/comments")
    def comment(pid):
        u,e=auth()
        if e:return e
        p=db.session.get(Post,pid)
        if not p:return {"error":"post_not_found"},404
        if not GroupMembership.query.filter_by(group_id=p.group_id,user_id=u.id,status="active").first():return {"error":"forbidden"},403
        body=(request.get_json(silent=True) or {}).get("body","").strip()
        if not body:return {"error":"body_required"},400
        db.session.add(Comment(post_id=pid,author_id=u.id,body=body));db.session.commit();return {"status":"created"},201
    @app.post("/api/v1/posts/<int:pid>/reactions")
    def react(pid):
        u,e=auth()
        if e:return e
        d=request.get_json(silent=True) or {}; r=Reaction.query.filter_by(post_id=pid,user_id=u.id).first()
        if r:r.reaction=d.get("reaction","like")
        else:db.session.add(Reaction(post_id=pid,user_id=u.id,reaction=d.get("reaction","like")))
        db.session.commit();return {"status":"ok"}
    @app.get("/api/v1/notifications")
    def notifications():
        u,e=auth()
        if e:return e
        ns=Notification.query.filter_by(user_id=u.id).order_by(Notification.created_at.desc()).limit(50).all()
        return {"items":[{"id":n.id,"kind":n.kind,"title":n.title,"body":n.body,"read":n.is_read,"created_at":n.created_at.isoformat()} for n in ns]}

    @app.post("/api/v1/auth/logout")
    def logout():
        u,e=auth()
        if e:return e
        h=request.headers.get("Authorization",""); t=h[7:] if h.startswith("Bearer ") else ""
        row=AuthToken.query.filter_by(token=t,user_id=u.id).first()
        if row: row.revoked=True; db.session.commit()
        return {"status":"logged_out"}
    @app.put("/api/v1/profile")
    def update_profile():
        u,e=auth()
        if e:return e
        d=request.get_json(silent=True) or {}; p=u.profile
        for k in ("full_name","phone","address","bio","profile_photo_url","institution_text","department","program","student_id"):
            if k in d: setattr(p,k,d[k])
        if "username" in d:
            name=str(d["username"]).strip().lower()
            if name and name!=p.username and UserProfile.query.filter_by(username=name).first(): return {"error":"username_exists"},409
            if name:p.username=name
        p.is_complete=all(getattr(p,k) for k in ("full_name","username","phone","address","institution_text","department","program","student_id"))
        db.session.commit(); return {"profile_complete":p.is_complete}
    @app.get("/api/v1/institutions/<int:iid>/departments")
    def departments(iid):
        return {"items":[{"id":d.id,"name":d.name,"code":d.code} for d in Department.query.filter_by(institution_id=iid).order_by(Department.name).all()]}
    @app.post("/api/v1/institutions/<int:iid>/departments")
    def create_department(iid):
        u,e=auth()
        if e:return e
        m=InstitutionMembership.query.filter_by(institution_id=iid,user_id=u.id,status="active").first()
        if not m or m.role not in MANAGERS:return {"error":"forbidden"},403
        d=request.get_json(silent=True) or {}
        if not d.get("name") or not d.get("code"):return {"error":"name_and_code_required"},400
        dep=Department(institution_id=iid,name=d["name"].strip(),code=d["code"].strip().upper()); db.session.add(dep); db.session.commit(); return {"id":dep.id},201
    @app.get("/api/v1/institutions/<int:iid>/requests")
    def list_join_requests(iid):
        u,e=auth()
        if e:return e
        m=InstitutionMembership.query.filter_by(institution_id=iid,user_id=u.id,status="active").first()
        if not m or m.role not in MANAGERS:return {"error":"forbidden"},403
        rs=JoinRequest.query.filter_by(institution_id=iid).order_by(JoinRequest.created_at.desc()).all()
        return {"items":[{"id":r.id,"user_id":r.user_id,"department_id":r.department_id,"student_id":r.student_id,"program":r.program,"session":r.session,"academic_year":r.academic_year,"status":r.status,"note":r.note} for r in rs]}
    @app.post("/api/v1/join-requests/<int:rid>/review")
    def review_join_request(rid):
        u,e=auth()
        if e:return e
        r=db.session.get(JoinRequest,rid)
        if not r:return {"error":"request_not_found"},404
        m=InstitutionMembership.query.filter_by(institution_id=r.institution_id,user_id=u.id,status="active").first()
        if not m or m.role not in MANAGERS:return {"error":"forbidden"},403
        d=request.get_json(silent=True) or {}; decision=d.get("decision")
        if decision not in ("approve","reject"):return {"error":"decision_required"},400
        if r.status!="pending":return {"error":"already_reviewed"},409
        r.status="approved" if decision=="approve" else "rejected"; r.reviewed_by=u.id
        if decision=="approve":
            db.session.add(InstitutionMembership(institution_id=r.institution_id,user_id=r.user_id,role="student",status="active",student_id=r.student_id,program=r.program))
            for g in Group.query.filter_by(institution_id=r.institution_id).all():
                db.session.add(GroupMembership(group_id=g.id,user_id=r.user_id,role="member",status="active"))
        db.session.commit(); return {"status":r.status}

    return app

app=create_app()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
