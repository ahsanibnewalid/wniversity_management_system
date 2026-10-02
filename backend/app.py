from backend.core import create_app as _create_core_app, db
from backend import academic, life, comms

def create_app():
    app=_create_core_app()
    academic.register(app)
    life.register(app)
    comms.register(app)
    with app.app_context():
        db.create_all()
    return app

app=create_app()
