import os
from flask import Flask, redirect, url_for, session, g
from flask_migrate import Migrate
from src.config import config
from src.models import db, User

migrate = Migrate()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    # Inyección de usuario actual en contexto de plantillas Jinja2
    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            g.current_user = None
        else:
            g.current_user = db.session.get(User, user_id)

    @app.context_processor
    def inject_user():
        return dict(current_user=getattr(g, "current_user", None))

    # Ruta raíz
    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("tasks.list_tasks"))
        return redirect(url_for("auth.login"))

    # Registro de Blueprints
    from src.routes.auth_routes import auth_bp
    from src.routes.task_routes import task_bp
    from src.routes.category_routes import category_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp, url_prefix="/tasks")
    app.register_blueprint(category_bp, url_prefix="/categories")

    return app
