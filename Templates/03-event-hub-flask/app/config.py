import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///instance/event_hub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = False

