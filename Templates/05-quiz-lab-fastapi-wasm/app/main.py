from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import database_path, init_db, seed_db
from app.repositories.quiz_repository import QuizRepository
from app.routes.api import router as api_router
from app.services.quiz_service import QuizService


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    db_path = database_path()
    init_db(db_path)
    seed_db(db_path)
    app.state.quiz_service = QuizService(QuizRepository(db_path))

    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()

