from functools import wraps
from flask import request, jsonify
from backend.core import db, User, AuthToken, InstitutionMembership, MANAGERS

def current_user():
    h=request.headers.get("Authorization","")
    token=h[7:] if h.startswith("Bearer ") else ""
    row=AuthToken.query.filter_by(token=token,revoked=False).first()
    return db.session.get(User,row.user_id) if row else None

def login_required(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        u=current_user()
        if not u:return jsonify(error="authentication_required"),401
        request.current_user=u
        return fn(*args,**kwargs)
    return wrapped

def institution_manager(iid):
    u=current_user()
    if not u:return False
    m=InstitutionMembership.query.filter_by(institution_id=iid,user_id=u.id,status="active").first()
    return bool(m and m.role in MANAGERS)
