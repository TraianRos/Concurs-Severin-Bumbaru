import os

from fastapi.testclient import TestClient

from app.database import init_db, seed_db


def create_test_client(tmp_path):
    db_path = tmp_path / "quiz_lab_test.db"
    init_db(str(db_path))
    seed_db(str(db_path))
    os.environ["DATABASE_PATH"] = str(db_path)

    from app.main import create_app

    app = create_app()
    return TestClient(app)


def test_health_and_submission(tmp_path):
    client = create_test_client(tmp_path)

    health = client.get("/api/health")
    assert health.status_code == 200

    quizzes = client.get("/api/quizzes")
    assert quizzes.status_code == 200
    quiz_id = quizzes.json()[0]["id"]

    quiz = client.get(f"/api/quizzes/{quiz_id}")
    assert quiz.status_code == 200
    questions = quiz.json()["questions"]

    response = client.post(
        "/api/submissions",
        json={
            "quizId": quiz_id,
            "playerName": "Radu",
            "answers": [{"questionId": question["id"], "answer": question["correct_answer"]} for question in questions],
        },
    )

    assert response.status_code == 200
    assert response.json()["score"] > 0


def test_submission_rejects_blank_player_name(tmp_path):
    client = create_test_client(tmp_path)

    quizzes = client.get("/api/quizzes").json()
    quiz = client.get(f"/api/quizzes/{quizzes[0]['id']}").json()

    response = client.post(
        "/api/submissions",
        json={
            "quizId": quiz["id"],
            "playerName": "   ",
            "answers": [{"questionId": question["id"], "answer": "x"} for question in quiz["questions"]],
        },
    )

    assert response.status_code == 400
