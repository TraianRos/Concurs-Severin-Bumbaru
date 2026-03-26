import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret")
    # Pentru SQLite, o cale relativa este interpretata de Flask fata de folderul `instance`.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///aplicatie_sesizari.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    APP_NAME = "Orasul in AlertA"
    PHOTO_MAX_FILES = 3
    PHOTO_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    PHOTO_MAX_TOTAL_SIZE_BYTES = (PHOTO_MAX_FILES * PHOTO_MAX_FILE_SIZE_BYTES) + (2 * 1024 * 1024)
    MAX_CONTENT_LENGTH = PHOTO_MAX_TOTAL_SIZE_BYTES
    PHOTO_UPLOAD_SUBDIR = "uploads/incidents"
    PHOTO_PROCESSING_STATUS_READY = "processed-jpeg-v1"
    MAP_DEFAULT_LAT = float(os.environ.get("MAP_DEFAULT_LAT", "45.4420"))
    MAP_DEFAULT_LNG = float(os.environ.get("MAP_DEFAULT_LNG", "28.0374"))
    MAP_DEFAULT_ZOOM = int(os.environ.get("MAP_DEFAULT_ZOOM", "13"))
