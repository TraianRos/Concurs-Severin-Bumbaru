from app.database import connect


class QuizRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def list_quizzes(self) -> list[dict]:
        with connect(self.db_path) as connection:
            rows = connection.execute("SELECT id, title, topic FROM quizzes ORDER BY title").fetchall()
            return [dict(row) for row in rows]

    def get_quiz(self, quiz_id: int) -> dict | None:
        with connect(self.db_path) as connection:
            quiz = connection.execute(
                "SELECT id, title, topic FROM quizzes WHERE id = ?",
                (quiz_id,),
            ).fetchone()

            if quiz is None:
                return None

            questions = connection.execute(
                """
                SELECT id, prompt, correct_answer, points
                FROM questions
                WHERE quiz_id = ?
                ORDER BY id
                """,
                (quiz_id,),
            ).fetchall()

            payload = dict(quiz)
            payload["questions"] = [dict(row) for row in questions]
            return payload

    def create_submission(self, quiz_id: int, player_name: str, score: int) -> dict:
        with connect(self.db_path) as connection:
            connection.execute(
                "INSERT INTO submissions (quiz_id, player_name, score) VALUES (?, ?, ?)",
                (quiz_id, player_name, score),
            )
            connection.commit()

            row = connection.execute(
                """
                SELECT id, quiz_id, player_name, score, submitted_at
                FROM submissions
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            return dict(row)

    def leaderboard(self) -> list[dict]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT s.id, q.title AS quiz_title, s.player_name, s.score, s.submitted_at
                FROM submissions s
                JOIN quizzes q ON q.id = s.quiz_id
                ORDER BY s.score DESC, s.submitted_at ASC
                LIMIT 10
                """
            ).fetchall()
            return [dict(row) for row in rows]

