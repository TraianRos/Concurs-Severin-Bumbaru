from pathlib import Path

from flask import Flask

from app.config import Config
from app.extensions import db, login_manager
from app.models import (
    INCIDENT_PRIORITY_CHOICES,
    INCIDENT_STATUS_CHOICES,
    PRIORITY_LABELS,
    ROLE_CHOICES,
    ROLE_LABELS,
    STATUS_LABELS,
    User,
)


def normalize_sqlite_uri(database_uri: str, instance_path: str) -> str:
    prefix = "sqlite:///"
    if not database_uri.startswith(prefix):
        return database_uri

    raw_path = database_uri[len(prefix):]
    if not raw_path or raw_path.startswith("/"):
        return database_uri

    # Acceptam si vechea forma `sqlite:///instance/...` si o transformam in calea corecta.
    if raw_path.startswith("instance/"):
        raw_path = raw_path.removeprefix("instance/")

    db_path = Path(instance_path) / raw_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config())

    if config_overrides:
        app.config.update(config_overrides)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_sqlite_uri(
        app.config["SQLALCHEMY_DATABASE_URI"],
        app.instance_path,
    )

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        # Flask-Login cere o functie care stie sa reconstruiasca utilizatorul din sesiune.
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_globals():
        # Punem aceste liste direct in template-uri ca sa nu repetam aceleasi select-uri in fiecare ruta.
        return {
            "role_choices": ROLE_CHOICES,
            "role_labels": ROLE_LABELS,
            "priority_choices": INCIDENT_PRIORITY_CHOICES,
            "priority_labels": PRIORITY_LABELS,
            "status_choices": INCIDENT_STATUS_CHOICES,
            "status_labels": STATUS_LABELS,
        }

    with app.app_context():
        db.create_all()

    from app.routes import api_bp, web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    return app
