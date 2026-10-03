from backend.core import create_app as _create_core_app, db
from backend import academic, life, comms, platform, admin, advanced, extra

def create_app(config=None):
    app=_create_core_app(config)
    academic.register(app)
    life.register(app)
    comms.register(app)
    comms.register_dashboard(app)
    platform.register(app)
    admin.register(app)
    admin.admin_academic_routes(app)
    advanced.register(app)
    extra.register(app)
    with app.app_context():
        db.create_all()
    return app

app=create_app()
