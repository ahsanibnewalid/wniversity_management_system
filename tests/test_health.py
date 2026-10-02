from backend.app import create_app

def test_health():
    app=create_app()
    response=app.test_client().get('/healthz')
    assert response.status_code==200
    assert response.json['status']=='ok'
