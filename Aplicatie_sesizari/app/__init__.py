from pathlib import Path

from flask import Flask, url_for
from flask_login import current_user
from sqlalchemy import inspect, text

from app.config import Config
from app.extensions import db, login_manager
from app.models import (
    INCIDENT_PRIORITY_CHOICES,
    INCIDENT_STATUS_CHOICES,
    STATUS_COUNT_LABELS,
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


def _rebuild_categories_table_for_optional_default_department() -> None:
    with db.engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("ALTER TABLE incident_categories RENAME TO incident_categories_legacy")
        connection.exec_driver_sql(
            """
            CREATE TABLE incident_categories (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(120) NOT NULL UNIQUE,
                description TEXT NOT NULL,
                default_department_id INTEGER,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(default_department_id) REFERENCES departments (id)
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO incident_categories (id, name, description, default_department_id, created_at)
            SELECT id, name, description, default_department_id, created_at
            FROM incident_categories_legacy
            """
        )
        connection.exec_driver_sql("DROP TABLE incident_categories_legacy")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()


def _rebuild_incidents_table(*, has_suggested_department_id: bool) -> None:
    suggested_department_select = (
        "suggested_department_id"
        if has_suggested_department_id
        else "NULL AS suggested_department_id"
    )

    with db.engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("ALTER TABLE incidents RENAME TO incidents_legacy")
        connection.exec_driver_sql(
            """
            CREATE TABLE incidents (
                id INTEGER NOT NULL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                address VARCHAR(255) NOT NULL,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                priority VARCHAR(32) NOT NULL,
                status VARCHAR(32) NOT NULL,
                created_by_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                suggested_department_id INTEGER,
                assigned_department_id INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(created_by_id) REFERENCES users (id),
                FOREIGN KEY(category_id) REFERENCES incident_categories (id),
                FOREIGN KEY(suggested_department_id) REFERENCES departments (id),
                FOREIGN KEY(assigned_department_id) REFERENCES departments (id)
            )
            """
        )
        connection.exec_driver_sql(
            f"""
            INSERT INTO incidents (
                id,
                title,
                description,
                address,
                latitude,
                longitude,
                priority,
                status,
                created_by_id,
                category_id,
                suggested_department_id,
                assigned_department_id,
                created_at,
                updated_at
            )
            SELECT
                id,
                title,
                description,
                address,
                latitude,
                longitude,
                priority,
                status,
                created_by_id,
                category_id,
                {suggested_department_select},
                assigned_department_id,
                created_at,
                updated_at
            FROM incidents_legacy
            """
        )
        connection.exec_driver_sql("DROP TABLE incidents_legacy")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()


def ensure_schema_compatibility() -> None:
    if db.engine.dialect.name != "sqlite":
        inspector = inspect(db.engine)
        if inspector.has_table("incidents"):
            incident_columns = {column["name"] for column in inspector.get_columns("incidents")}
            if "suggested_department_id" not in incident_columns:
                db.session.execute(text("ALTER TABLE incidents ADD COLUMN suggested_department_id INTEGER"))
        if inspector.has_table("incident_photos"):
            photo_columns = {column["name"] for column in inspector.get_columns("incident_photos")}
            if "is_pertinent" not in photo_columns:
                db.session.execute(
                    text("ALTER TABLE incident_photos ADD COLUMN is_pertinent BOOLEAN NOT NULL DEFAULT 0")
                )
        db.session.commit()
        return

    inspector = inspect(db.engine)

    if inspector.has_table("incident_categories"):
        category_columns = {
            column["name"]: column for column in inspector.get_columns("incident_categories")
        }
        if not category_columns["default_department_id"]["nullable"]:
            _rebuild_categories_table_for_optional_default_department()
            inspector = inspect(db.engine)

    if inspector.has_table("incidents"):
        incident_columns = {column["name"]: column for column in inspector.get_columns("incidents")}
        needs_rebuild = (
            "suggested_department_id" not in incident_columns
            or not incident_columns["assigned_department_id"]["nullable"]
        )
        if needs_rebuild:
            _rebuild_incidents_table(
                has_suggested_department_id="suggested_department_id" in incident_columns
            )
            inspector = inspect(db.engine)

    if inspector.has_table("incident_photos"):
        photo_columns = {column["name"] for column in inspector.get_columns("incident_photos")}
        if "is_pertinent" not in photo_columns:
            db.session.execute(
                text("ALTER TABLE incident_photos ADD COLUMN is_pertinent BOOLEAN NOT NULL DEFAULT 0")
            )
            db.session.commit()


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
        def static_asset(filename: str) -> str:
            asset_path = Path(app.static_folder) / filename
            version = int(asset_path.stat().st_mtime) if asset_path.exists() else 0
            return url_for("static", filename=filename, v=version)

        def user_display_name(user) -> str:
            if not current_user.is_authenticated:
                return "Utilizator anonim"
            if current_user.role in ["dispatcher", "admin"] or current_user.id == user.id:
                return user.full_name

            anonymized_labels = {
                "citizen": "Cetatean anonim",
                "operator": "Operator local",
                "dispatcher": "Dispecer platforma",
                "admin": "Administrator platforma",
            }
            return anonymized_labels.get(user.role, "Utilizator anonim")

        return {
            "role_choices": ROLE_CHOICES,
            "role_labels": ROLE_LABELS,
            "priority_choices": INCIDENT_PRIORITY_CHOICES,
            "priority_labels": PRIORITY_LABELS,
            "status_choices": INCIDENT_STATUS_CHOICES,
            "status_count_labels": STATUS_COUNT_LABELS,
            "status_labels": STATUS_LABELS,
            "static_asset": static_asset,
            "user_display_name": user_display_name,
        }

    with app.app_context():
        db.create_all()
        ensure_schema_compatibility()

    from app.routes import api_bp, web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    return app
