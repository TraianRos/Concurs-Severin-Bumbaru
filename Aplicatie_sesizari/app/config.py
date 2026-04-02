import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret")
    # Pentru SQLite, o cale relativa este interpretata de Flask fata de folderul `instance`.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///aplicatie_sesizari.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    APP_NAME = "Orașul în Alertă"
    PHOTO_MAX_FILES = 3
    PHOTO_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    PHOTO_MAX_TOTAL_SIZE_BYTES = (PHOTO_MAX_FILES * PHOTO_MAX_FILE_SIZE_BYTES) + (2 * 1024 * 1024)
    MAX_CONTENT_LENGTH = PHOTO_MAX_TOTAL_SIZE_BYTES
    PHOTO_UPLOAD_SUBDIR = "uploads/incidents"
    PHOTO_PROCESSING_STATUS_READY = "processed-jpeg-v1"
    MAP_DEFAULT_LAT = float(os.environ.get("MAP_DEFAULT_LAT", "45.4420"))
    MAP_DEFAULT_LNG = float(os.environ.get("MAP_DEFAULT_LNG", "28.0374"))
    MAP_DEFAULT_ZOOM = int(os.environ.get("MAP_DEFAULT_ZOOM", "13"))
    FORM_LIMITS = {
        "full_name": 120,
        "email": 255,
        "password": 128,
        "incident_title": 200,
        "incident_address": 255,
        "incident_description": 2000,
        "incident_report_details": 1000,
        "incident_search": 120,
    }
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
    SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes", "on"}
    SMTP_TIMEOUT_SECONDS = float(os.environ.get("SMTP_TIMEOUT_SECONDS", "10"))
    EMAIL_SUBJECT_PREFIX = os.environ.get("EMAIL_SUBJECT_PREFIX", APP_NAME)
    WEB_PUSH_PUBLIC_KEY = os.environ.get("WEB_PUSH_PUBLIC_KEY", "")
    WEB_PUSH_PRIVATE_KEY = os.environ.get("WEB_PUSH_PRIVATE_KEY", "")
    WEB_PUSH_SUBJECT = os.environ.get("WEB_PUSH_SUBJECT", "mailto:demo@example.com")
    INCIDENT_AUTO_HIDE_REPORT_THRESHOLD = int(os.environ.get("INCIDENT_AUTO_HIDE_REPORT_THRESHOLD", "5"))
