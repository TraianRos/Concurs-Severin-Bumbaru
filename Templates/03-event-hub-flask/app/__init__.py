from pathlib import Path

from flask import Flask

from app.config import Config
from app.extensions import db


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config())

    if config_overrides:
        app.config.update(config_overrides)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.routes.web import web_bp

    app.register_blueprint(web_bp)
    return app

