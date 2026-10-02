from functools import wraps
from flask import request, jsonify
from backend.core import (
    db, User, UserProfile, Institution, InstitutionMembership, Department,
    AcademicSession, AcademicYear, Group, GroupMembership, JoinRequest, Notification,
    MANAGERS
)
from backend.api import login_required, current_user

ROLE_PERMISSIONS = {
    "institution_owner": {"institution.manage","members.manage","academics.manage","content.manage","finance.manage","requests.manage","groups.manage","analytics.view"},
    "institution_admin": {"institution.manage","members.manage","academics.manage","content.manage","finance.manage","requests.manage","groups.manage","analytics.view"},
    "principal": {"institution.manage","members.manage","academics.manage","content.manage","requests.manage","groups.manage","analytics.view"},
    "department_admin": {"academics.manage","members.manage","content.manage","requests.manage","analytics.view"},
    "teacher": {"academics.teach","content.manage"},
    "media_manager": {"content.manage"},
    "class_representative": {"groups.manage","content.manage"},
    "student": set(),
}

def row(x):
    return {c.name: getattr(x, c.name) for c in x.__table__.columns}

def membership(iid, uid=None):
    uid = uid or request.current_user.id
    return InstitutionMembership.query.filter_by(institution_id=iid, user_id=uid, status="active").first()

def has_permission(iid, permission):
    m = membership(iid)
    return bool(m and permission in ROLE_PERMISSIONS.get(m.role, set()))

def require_permission(permission):
    def deco(fn):
        @wraps(fn)
        def wrapped(iid, *args, **kwargs):
            if not has_permission(iid, permission):
                return jsonify(error="forbidden", required_permission=permission), 403
            return fn(iid, *args, **kwargs)
        return wrapped
    return deco

def register(app):
    @app.get("/api/v1/admin/institutions")
    @login_required
    def my_admin_institutions():
        uid=request.current_user.id
        ms=InstitutionMembership.query.filter_by(user_id=uid,status="active").all()
        items=[]
        for m in ms:
            if m.role in MANAGERS or m.role=="department_admin":
                i=db.session.get(Institution,m.institution_id)
                if i: items.append({**row(i),"role":m.role})
        return jsonify(items=items)

    @app.get("/api/v1/institutions/<int:iid>/admin/overview")
    @login_required
    @require_permission("analytics.view")
    def overview(iid):
        i=db.get_or_404(Institution,iid)
        return jsonify(
            institution=row(i),
            role=membership(iid).role,
            counts={
                "members":InstitutionMembership.query.filter_by(institution_id=iid,status="active").count(),
                "departments":Department.query.filter_by(institution_id=iid).count(),
                "sessions":AcademicSession.query.join(Department, AcademicSession.department_id==Department.id).filter(Department.institution_id==iid).count(),
                "groups":Group.query.filter_by(institution_id=iid).count(),
                "pending_requests":JoinRequest.query.filter_by(institution_id=iid,status="pending").count(),
            }
        )

    @app.put("/api/v1/institutions/<int:iid>/admin/institution")
    @login_required
    @require_permission("institution.manage")
    def edit_institution(iid):
        i=db.get_or_404(Institution,iid); d=request.get_json() or {}
        for k in ("name","slug","kind","address","website","description"):
            if k in d and d[k] is not None: setattr(i,k,str(d[k]).strip())
        db.session.commit(); return jsonify(data=row(i))

    @app.get("/api/v1/institutions/<int:iid>/admin/members")
    @login_required
    @require_permission("members.manage")
    def members(iid):
        ms=InstitutionMembership.query.filter_by(institution_id=iid).all()
        items=[]
        for m in ms:
            u=db.session.get(User,m.user_id); p=db.session.get(UserProfile,m.user_id)
            items.append({**row(m),"email":u.email if u else None,"full_name":p.full_name if p else None,"username":p.username if p else None})
        return jsonify(items=items)

    @app.put("/api/v1/institutions/<int:iid>/admin/members/<int:mid>")
    @login_required
    @require_permission("members.manage")
    def edit_member(iid,mid):
        m=db.session.get(InstitutionMembership,mid)
        if not m or m.institution_id!=iid:return jsonify(error="membership_not_found"),404
        d=request.get_json() or {}; actor=membership(iid)
        role=d.get("role")
        if role:
            allowed=set(ROLE_PERMISSIONS)
            if role not in allowed:return jsonify(error="invalid_role"),400
            if actor.role!="institution_owner" and role=="institution_owner":return jsonify(error="owner_only"),403
            m.role=role
        for k in ("status","student_id","program"):
            if k in d and d[k] is not None:setattr(m,k,d[k])
        db.session.commit();return jsonify(data=row(m))

    @app.delete("/api/v1/institutions/<int:iid>/admin/members/<int:mid>")
    @login_required
    @require_permission("members.manage")
    def remove_member(iid,mid):
        m=db.session.get(InstitutionMembership,mid)
        if not m or m.institution_id!=iid:return jsonify(error="membership_not_found"),404
        if m.role=="institution_owner":return jsonify(error="owner_cannot_be_removed"),400
        m.status="suspended";db.session.commit();return jsonify(status="suspended")

    @app.post("/api/v1/institutions/<int:iid>/admin/members/invite")
    @login_required
    @require_permission("members.manage")
    def invite_member(iid):
        d=request.get_json() or {}; email=str(d.get("email","")).strip().lower()
        u=User.query.filter_by(email=email).first()
        if not u:return jsonify(error="user_not_found",message="The user must register before being added."),404
        if membership(iid,u.id):return jsonify(error="already_member"),409
        role=d.get("role","student")
        if role not in ROLE_PERMISSIONS:return jsonify(error="invalid_role"),400
        m=InstitutionMembership(institution_id=iid,user_id=u.id,role=role,status="active",student_id=d.get("student_id"),program=d.get("program"))
        db.session.add(m);db.session.add(Notification(user_id=u.id,kind="membership",title="Added to institution",body=f"You were added to institution #{iid} as {role}."));db.session.commit()
        return jsonify(data=row(m)),201

    @app.post("/api/v1/institutions/<int:iid>/admin/departments")
    @login_required
    @require_permission("academics.manage")
    def admin_add_department(iid):
        d=request.get_json() or {}
        if not d.get("name") or not d.get("code"):return jsonify(error="name_and_code_required"),400
        x=Department(institution_id=iid,name=d["name"].strip(),code=d["code"].strip().upper());db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.put("/api/v1/institutions/<int:iid>/admin/departments/<int:did>")
    @login_required
    @require_permission("academics.manage")
    def admin_edit_department(iid,did):
        x=db.session.get(Department,did)
        if not x or x.institution_id!=iid:return jsonify(error="department_not_found"),404
        d=request.get_json() or {}
        for k in ("name","code"):
            if k in d:setattr(x,k,str(d[k]).strip())
        db.session.commit();return jsonify(data=row(x))

    @app.delete("/api/v1/institutions/<int:iid>/admin/departments/<int:did>")
    @login_required
    @require_permission("academics.manage")
    def admin_delete_department(iid,did):
        x=db.session.get(Department,did)
        if not x or x.institution_id!=iid:return jsonify(error="department_not_found"),404
        if AcademicSession.query.filter_by(department_id=did).first():return jsonify(error="department_has_academic_sessions"),409
        db.session.delete(x);db.session.commit();return jsonify(status="deleted")

    @app.get("/api/v1/institutions/<int:iid>/admin/sessions")
    @login_required
    @require_permission("academics.manage")
    def sessions(iid):
        deps=Department.query.filter_by(institution_id=iid).all(); ids=[x.id for x in deps]
        items=[]
        for s in AcademicSession.query.filter(AcademicSession.department_id.in_(ids)).all() if ids else []:
            items.append({**row(s),"department_name":db.session.get(Department,s.department_id).name})
        return jsonify(items=items)

    @app.post("/api/v1/institutions/<int:iid>/admin/sessions")
    @login_required
    @require_permission("academics.manage")
    def add_session(iid):
        d=request.get_json() or {}; dep=db.session.get(Department,d.get("department_id"))
        if not dep or dep.institution_id!=iid:return jsonify(error="department_not_found"),404
        x=AcademicSession(department_id=dep.id,name=d.get("name","").strip())
        if not x.name:return jsonify(error="name_required"),400
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.post("/api/v1/institutions/<int:iid>/admin/years")
    @login_required
    @require_permission("academics.manage")
    def add_year(iid):
        d=request.get_json() or {}; s=db.session.get(AcademicSession,d.get("session_id"))
        if not s:return jsonify(error="session_not_found"),404
        dep=db.session.get(Department,s.department_id)
        if not dep or dep.institution_id!=iid:return jsonify(error="forbidden"),403
        x=AcademicYear(session_id=s.id,name=d.get("name","").strip());db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.get("/api/v1/institutions/<int:iid>/admin/groups")
    @login_required
    @require_permission("groups.manage")
    def admin_groups(iid):
        return jsonify(items=[row(x) for x in Group.query.filter_by(institution_id=iid).order_by(Group.name).all()])

    @app.post("/api/v1/institutions/<int:iid>/admin/groups")
    @login_required
    @require_permission("groups.manage")
    def admin_add_group(iid):
        d=request.get_json() or {};x=Group(institution_id=iid,department_id=d.get("department_id"),session_id=d.get("session_id"),academic_year_id=d.get("academic_year_id"),name=d.get("name","").strip(),group_type=d.get("group_type","community"),description=d.get("description",""),is_private=bool(d.get("is_private",False)))
        if not x.name:return jsonify(error="name_required"),400
        db.session.add(x);db.session.commit();return jsonify(data=row(x)),201

    @app.put("/api/v1/institutions/<int:iid>/admin/groups/<int:gid>")
    @login_required
    @require_permission("groups.manage")
    def admin_edit_group(iid,gid):
        x=db.session.get(Group,gid)
        if not x or x.institution_id!=iid:return jsonify(error="group_not_found"),404
        d=request.get_json() or {}
        for k in ("name","group_type","description","is_private","department_id","session_id","academic_year_id"):
            if k in d:setattr(x,k,d[k])
        db.session.commit();return jsonify(data=row(x))

    @app.delete("/api/v1/institutions/<int:iid>/admin/groups/<int:gid>")
    @login_required
    @require_permission("groups.manage")
    def admin_delete_group(iid,gid):
        x=db.session.get(Group,gid)
        if not x or x.institution_id!=iid:return jsonify(error="group_not_found"),404
        GroupMembership.query.filter_by(group_id=gid).delete()
        db.session.delete(x);db.session.commit();return jsonify(status="deleted")

    @app.get("/api/v1/institutions/<int:iid>/admin/requests")
    @login_required
    @require_permission("requests.manage")
    def admin_requests(iid):
        return jsonify(items=[row(x) for x in JoinRequest.query.filter_by(institution_id=iid).order_by(JoinRequest.created_at.desc()).all()])

    @app.post("/api/v1/institutions/<int:iid>/admin/requests/<int:rid>/review")
    @login_required
    @require_permission("requests.manage")
    def admin_review_request(iid,rid):
        r=db.session.get(JoinRequest,rid)
        if not r or r.institution_id!=iid:return jsonify(error="request_not_found"),404
        d=request.get_json() or {}; decision=d.get("decision")
        if decision not in ("approve","reject"):return jsonify(error="decision_required"),400
        if r.status!="pending":return jsonify(error="already_reviewed"),409
        r.status="approved" if decision=="approve" else "rejected";r.reviewed_by=request.current_user.id
        if decision=="approve":
            old=membership(iid,r.user_id)
            if old: old.status="active";old.student_id=r.student_id;old.program=r.program
            else: db.session.add(InstitutionMembership(institution_id=iid,user_id=r.user_id,role="student",status="active",student_id=r.student_id,program=r.program))
            db.session.add(Notification(user_id=r.user_id,kind="membership",title="Join request approved",body=f"Your request to join institution #{iid} was approved."))
        db.session.commit();return jsonify(status=r.status)

    @app.get("/api/v1/institutions/<int:iid>/admin/permissions")
    @login_required
    @require_permission("members.manage")
    def permissions(iid):
        return jsonify(roles={k:sorted(v) for k,v in ROLE_PERMISSIONS.items()})

    @app.get("/api/v1/institutions/<int:iid>/admin")
    @login_required
    @require_permission("analytics.view")
    def admin_home(iid):
        i=db.get_or_404(Institution,iid);m=membership(iid)
        return jsonify(institution=row(i),role=m.role,permissions=sorted(ROLE_PERMISSIONS.get(m.role,set())))

