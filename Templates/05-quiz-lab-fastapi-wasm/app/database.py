from pathlib import Path
import os
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"


def database_path() -> str:
    configured = os.environ.get("DATABASE_PATH", "./quiz_lab.db")
    return str((BASE_DIR / configured).resolve()) if not os.path.isabs(configured) else configured


def connect(db_path: str | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path or database_path())
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str | None = None) -> None:
    connection = connect(db_path)
    schema = (DB_DIR / "schema.sql").read_text()
    connection.executescript(schema)
    connection.commit()
    connection.close()


def seed_db(db_path: str | None = None) -> None:
    connection = connect(db_path)
    existing = connection.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]

    if existing == 0:
        connection.executescript((DB_DIR / "seed.sql").read_text())
        connection.commit()

    connection.close()

