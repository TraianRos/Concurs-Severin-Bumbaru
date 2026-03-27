from app.extensions import db
from app.models.entities import IncidentVote


class IncidentVoteRepository:
    def find_for_user(self, incident_id: int, user_id: int) -> IncidentVote | None:
        return IncidentVote.query.filter_by(incident_id=incident_id, user_id=user_id).first()

    def create(self, incident_id: int, user_id: int) -> IncidentVote:
        vote = IncidentVote(incident_id=incident_id, user_id=user_id)
        db.session.add(vote)
        db.session.flush()
        return vote

    def delete(self, vote: IncidentVote) -> None:
        db.session.delete(vote)
