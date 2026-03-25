from pydantic import BaseModel, Field


class AnswerIn(BaseModel):
    questionId: int = Field(gt=0)
    answer: str


class SubmissionIn(BaseModel):
    quizId: int = Field(gt=0)
    playerName: str
    answers: list[AnswerIn]

