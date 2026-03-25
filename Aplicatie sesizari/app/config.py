import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret")
    # Pentru SQLite, o cale relativa este interpretata de Flask fata de folderul `instance`.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///aplicatie_sesizari.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    APP_NAME = "Orasul in AlertA"
    MAP_DEFAULT_LAT = float(os.environ.get("MAP_DEFAULT_LAT", "44.6369"))
    MAP_DEFAULT_LNG = float(os.environ.get("MAP_DEFAULT_LNG", "22.6597"))
    MAP_DEFAULT_ZOOM = int(os.environ.get("MAP_DEFAULT_ZOOM", "13"))
