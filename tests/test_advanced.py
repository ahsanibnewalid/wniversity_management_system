from backend.app import create_app
from backend.core import db

def client():
    app=create_app()
    app.config.update(TESTING=True,SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app.test_client()

def register_login(c,email="advanced@example.com"):
    r=c.post("/api/v1/auth/register",json={"email":email,"password":"password123","full_name":"Advanced User","username":email.split("@")[0]})
    assert r.status_code==201
    r=c.post("/api/v1/auth/login",json={"email":email,"password":"password123"})
    assert r.status_code==200
    return {"Authorization":"Bearer "+r.json["access_token"]}

def test_advanced_health_and_summary():
    c=client();h=register_login(c)
    r=c.get("/api/v1/me/academic-summary",headers=h)
    assert r.status_code==200
    assert r.json["cgpa"]==0

def test_password_reset_and_logout_all():
    c=client();h=register_login(c,"reset@example.com")
    r=c.post("/api/v1/auth/password-reset/request",json={"email":"reset@example.com"})
    assert r.status_code==200 and r.json["token"]
    r=c.post("/api/v1/auth/password-reset/confirm",json={"token":r.json["token"],"password":"newpassword123"})
    assert r.status_code==200
    r=c.post("/api/v1/auth/login",json={"email":"reset@example.com","password":"newpassword123"})
    assert r.status_code==200
    h2={"Authorization":"Bearer "+r.json["access_token"]}
    assert c.post("/api/v1/auth/logout-all",headers=h2).status_code==200
    assert c.get("/api/v1/auth/me",headers=h2).status_code==401

def test_push_and_verification():
    c=client();h=register_login(c,"mobile@example.com")
    assert c.post("/api/v1/push/devices",json={"token":"ExponentPushToken[test]"},headers=h).status_code==200
    assert c.post("/api/v1/profile/verification/confirm",json={"code":"000000"},headers=h).status_code==200
    assert c.get("/api/v1/profile/verification",headers=h).json["verified"] is True


def test_advanced_routes_are_registered():
    c=client();h=register_login(c,"routes@example.com")
    assert c.get("/api/v1/teacher/dashboard",headers=h).status_code==200
    assert c.get("/api/v1/academic-calendar",headers=h).status_code==200
    assert c.get("/api/v1/library/my-loans",headers=h).status_code==200
    assert c.get("/api/v1/search/all?q=test",headers=h).status_code==200
    assert c.get("/api/v1/profile/verification",headers=h).status_code==200
