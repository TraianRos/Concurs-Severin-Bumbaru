class QuizService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def list_quizzes(self) -> list[dict]:
        return self.repository.list_quizzes()

    def get_quiz(self, quiz_id: int) -> dict | None:
        return self.repository.get_quiz(quiz_id)

    def submit(self, payload) -> dict:
        quiz = self.repository.get_quiz(payload.quizId)
        if quiz is None:
            raise ValueError("Quiz not found.")

        player_name = payload.playerName.strip()
        if not player_name:
            raise ValueError("Player name is required.")

        answer_map = {answer.questionId: answer.answer.strip().lower() for answer in payload.answers}

        score = 0
        for question in quiz["questions"]:
            expected = question["correct_answer"].strip().lower()
            actual = answer_map.get(question["id"], "")
            if actual == expected:
                score += int(question["points"])

        submission = self.repository.create_submission(payload.quizId, player_name, score)
        return {"submission": submission, "score": score}

    def leaderboard(self) -> list[dict]:
        return self.repository.leaderboard()

