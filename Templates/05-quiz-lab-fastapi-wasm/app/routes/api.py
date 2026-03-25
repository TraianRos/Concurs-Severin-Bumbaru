from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import SubmissionIn

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok", "app": "quiz-lab"}


@router.get("/quizzes")
def list_quizzes(request: Request):
    return request.app.state.quiz_service.list_quizzes()


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int, request: Request):
    quiz = request.app.state.quiz_service.get_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz


@router.post("/submissions")
def create_submission(payload: SubmissionIn, request: Request):
    try:
        return request.app.state.quiz_service.submit(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/leaderboard")
def leaderboard(request: Request):
    return request.app.state.quiz_service.leaderboard()

