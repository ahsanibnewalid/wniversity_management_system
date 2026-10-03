from backend.app import create_app
def test_health():
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":"sqlite://"})
    response=app.test_client().get("/healthz")
    assert response.status_code==200
    assert response.json["status"]=="ok"
def test_register_login_profile():
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":"sqlite://"})
    c=app.test_client()
    r=c.post("/api/v1/auth/register",json={"email":"test@example.com","password":"password123","full_name":"Test User","username":"testuser"})
    assert r.status_code==201
    r=c.post("/api/v1/auth/login",json={"email":"test@example.com","password":"password123"})
    assert r.status_code==200 and r.json["access_token"]
