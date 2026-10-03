from datetime import datetime,timezone
from flask import request,jsonify
from werkzeug.security import check_password_hash,generate_password_hash
from backend.core import (
    db,Notification,InstitutionMembership,JoinRequest,Institution,User,UserProfile,
    Department,Group,is_platform_admin
)
from backend.api import login_required,institution_manager
from backend.academic import Course,CourseOffering,Enrollment

class Announcement(db.Model):
    id=db.Column(db.Integer,primary_key=True);institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id"),nullable=False);author_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);title=db.Column(db.String(255),nullable=False);body=db.Column(db.Text,nullable=False);audience=db.Column(db.String(50),default="all");created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

def data(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}

def member_data(membership,user,institution):
    profile=db.session.get(UserProfile,user.id)
    return {
        **data(membership),"email":user.email,
        "full_name":profile.full_name if profile else None,
        "institution_name":institution.name,
        "is_institution_owner":institution.owner_id==user.id,
    }

PLATFORM_ROLES={
    "institution_owner","institution_admin","principal","dean","department_admin",
    "teacher","media_manager","class_representative","student",
}

def transfer_owner(institution,user_id):
    previous=InstitutionMembership.query.filter_by(
        institution_id=institution.id,user_id=institution.owner_id
    ).first()
    target=InstitutionMembership.query.filter_by(
        institution_id=institution.id,user_id=user_id
    ).first()
    if target:
        target.role="institution_owner"
        target.status="active"
    else:
        target=InstitutionMembership(
            institution_id=institution.id,user_id=user_id,
            role="institution_owner",status="active",
        )
        db.session.add(target)
    if previous and previous.user_id!=user_id:
        previous.role="institution_admin"
        previous.status="active"
    institution.owner_id=user_id
    return target

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
    @login_required
    def announcements(iid):
        membership=InstitutionMembership.query.filter_by(
            institution_id=iid,user_id=request.current_user.id,status="active"
        ).first()
        if not membership:return jsonify(error="institution_membership_required"),403
        visible={"all"}
        if membership.role=="student":visible.add("students")
        elif membership.role=="teacher":visible.update(("teachers","staff"))
        else:visible.update(("staff","admins"))
        items=Announcement.query.filter(
            Announcement.institution_id==iid,Announcement.audience.in_(visible)
        ).order_by(Announcement.created_at.desc()).all()
        return jsonify(items=[data(x) for x in items])
    @app.post("/api/v1/institutions/<int:iid>/announcements")
    @login_required
    def add_announcement(iid):
        if not institution_manager(iid):return jsonify(error="forbidden"),403
        d=request.get_json(silent=True) or {}
        title=str(d.get("title","")).strip()
        body=str(d.get("body","")).strip()
        audience=str(d.get("audience","all")).strip().lower()
        if not title or not body:return jsonify(error="title_and_body_required"),400
        if audience not in {"all","students","teachers","staff","admins"}:
            return jsonify(error="invalid_announcement_audience"),400
        x=Announcement(institution_id=iid,author_id=request.current_user.id,title=title,body=body,audience=audience);db.session.add(x)
        members=InstitutionMembership.query.filter_by(institution_id=iid,status="active").all()
        def receives(role):
            return audience=="all" or (audience=="students" and role=="student") or (audience=="teachers" and role=="teacher") or (audience=="staff" and role!="student") or (audience=="admins" and role in MANAGERS)
        for m in members:
            if receives(m.role):db.session.add(Notification(user_id=m.user_id,kind="announcement",title=x.title,body=x.body))
        db.session.commit();return jsonify(data(x)),201

    @app.get("/api/v1/platform/admin/overview")
    @login_required
    def platform_admin_overview():
        if not is_platform_admin(request.current_user):
            return jsonify(error="platform_admin_required"),403
        return jsonify(counts={
            "universities":Institution.query.count(),
            "users":User.query.count(),
            "memberships":InstitutionMembership.query.count(),
            "active_memberships":InstitutionMembership.query.filter_by(status="active").count(),
            "pending_requests":JoinRequest.query.filter_by(status="pending").count(),
            "departments":Department.query.count(),
            "courses":Course.query.count(),
            "course_offerings":CourseOffering.query.count(),
            "enrollments":Enrollment.query.filter_by(status="enrolled").count(),
            "groups":Group.query.count(),
        })

    @app.get("/api/v1/platform/admin/institutions")
    @login_required
    def platform_admin_institutions():
        if not is_platform_admin(request.current_user):
            return jsonify(error="platform_admin_required"),403
        active_counts=dict(db.session.query(
            InstitutionMembership.institution_id,db.func.count( InstitutionMembership.id)
        ).filter_by(status="active").group_by(InstitutionMembership.institution_id).all())
        pending_counts=dict(db.session.query(
            JoinRequest.institution_id,db.func.count(JoinRequest.id)
        ).filter_by(status="pending").group_by(JoinRequest.institution_id).all())
        items=[]
        for institution in Institution.query.order_by(Institution.name).limit(500).all():
            owner=db.session.get(User,institution.owner_id)
            items.append({
                **data(institution),
                "owner_email":owner.email if owner else None,
                "active_members":active_counts.get(institution.id,0),
                "pending_requests":pending_counts.get(institution.id,0),
            })
        return jsonify(items=items)

    @app.get("/api/v1/platform/admin/users")
    @login_required
    def platform_admin_users():
        if not is_platform_admin(request.current_user):
            return jsonify(error="platform_admin_required"),403
        query=str(request.args.get("q","")).strip()
        users_query=db.session.query(User,UserProfile).join(UserProfile,UserProfile.user_id==User.id)
        if query:
            pattern=f"%{query}%"
            users_query=users_query.filter(
                db.or_(User.email.ilike(pattern),UserProfile.full_name.ilike(pattern),
                       UserProfile.username.ilike(pattern))
            )
        items=[]
        for user,profile in users_query.order_by(User.id.desc()).limit(100).all():
            items.append({
                "id":user.id,"email":user.email,"full_name":profile.full_name,
                "username":profile.username,
                "memberships":InstitutionMembership.query.filter_by(user_id=user.id).count(),
                "active_memberships":InstitutionMembership.query.filter_by(
                    user_id=user.id,status="active"
                ).count(),
            })
        return jsonify(items=items)

    @app.get("/api/v1/platform/admin/members")
    @login_required
    def platform_admin_members():
        if not is_platform_admin(request.current_user):
            return jsonify(error="platform_admin_required"),403
        institution_id=request.args.get("institution_id",type=int)
        query=db.session.query(InstitutionMembership,User,UserProfile,Institution).join(
            User,User.id==InstitutionMembership.user_id
        ).join(UserProfile,UserProfile.user_id==User.id).join(
            Institution,Institution.id==InstitutionMembership.institution_id
        )
        if institution_id:
            query=query.filter(InstitutionMembership.institution_id==institution_id)
        q=str(request.args.get("q","")).strip()
        if q:
            pattern=f"%{q}%"
            query=query.filter(db.or_(
                User.email.ilike(pattern),UserProfile.full_name.ilike(pattern),
                Institution.name.ilike(pattern),
            ))
        items=[]
        for membership,user,profile,institution in query.order_by(
            Institution.name,UserProfile.full_name
        ).limit(500).all():
            items.append({
                **data(membership),"email":user.email,"full_name":profile.full_name,
                "institution_name":institution.name,
                "is_institution_owner":institution.owner_id==user.id,
            })
        return jsonify(items=items,roles=sorted(PLATFORM_ROLES))

    @app.post("/api/v1/platform/admin/institutions/<int:iid>/members")
    @login_required
    def platform_admin_add_member(iid):
        if not is_platform_admin(request.current_user):
            return jsonify(error="platform_admin_required"),403
        institution=db.session.get(Institution,iid)
        if not institution:return jsonify(error="institution_not_found"),404
        d=request.get_json() or {}
        email=str(d.get("email","")).strip().lower()
        role=d.get("role","student")
        if not email:return jsonify(error="email_required"),400
        if not isinstance(role,str) or role not in PLATFORM_ROLES:
            return jsonify(error="invalid_role"),400
        user=User.query.filter_by(email=email).first()
        if not user:return jsonify(error="user_not_found"),404
        membership=InstitutionMembership.query.filter_by(
            institution_id=iid,user_id=user.id
        ).first()
        if role=="institution_owner":
            membership=transfer_owner(institution,user.id)
        elif membership:
            if membership.status=="active":return jsonify(error="already_member"),409
            membership.role=role;membership.status="active"
        else:
            membership=InstitutionMembership(
                institution_id=iid,user_id=user.id,role=role,status="active",
                student_id=d.get("student_id"),program=d.get("program"),
            )
            db.session.add(membership)
        db.session.commit()
        return jsonify(data=member_data(membership,user,institution)),201

    @app.patch("/api/v1/platform/admin/members/<int:mid>")
    @login_required
    def platform_admin_update_member(mid):
        if not is_platform_admin(request.current_user):
            return jsonify(error="platform_admin_required"),403
        membership=db.session.get(InstitutionMembership,mid)
        if not membership:return jsonify(error="membership_not_found"),404
        institution=db.session.get(Institution,membership.institution_id)
        user=db.session.get(User,membership.user_id)
        d=request.get_json() or {}
        role=d.get("role",membership.role)
        status=d.get("status","active" if role=="institution_owner" else membership.status)
        if not isinstance(role,str) or role not in PLATFORM_ROLES:
            return jsonify(error="invalid_role"),400
        if status not in {"active","suspended"}:
            return jsonify(error="invalid_status"),400
        if role=="institution_owner" and status!="active":
            return jsonify(error="owner_must_be_active"),400
        if role=="institution_owner":
            membership=transfer_owner(institution,user.id)
        elif institution.owner_id==user.id and (status!="active" or role!="institution_owner"):
            return jsonify(error="transfer_ownership_first"),409
        membership.role=role
        membership.status=status
        db.session.commit()
        return jsonify(data=member_data(membership,user,institution))
