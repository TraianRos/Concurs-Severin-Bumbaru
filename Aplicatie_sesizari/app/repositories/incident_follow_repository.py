from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.entities import IncidentFollow


class IncidentFollowRepository:
    def _base_query(self):
        return IncidentFollow.query.options(
            joinedload(IncidentFollow.user),
            joinedload(IncidentFollow.push_subscription),
        )

    def find_for_user(self, incident_id: int, user_id: int) -> IncidentFollow | None:
        return self._base_query().filter_by(incident_id=incident_id, user_id=user_id).first()

    def list_for_incident(self, incident_id: int) -> list[IncidentFollow]:
        return self._base_query().filter_by(incident_id=incident_id).all()

    def create_or_update(
        self,
        *,
        incident_id: int,
        user_id: int,
        in_app_enabled: bool,
        email_enabled: bool,
        push_subscription_id: int | None,
    ) -> IncidentFollow:
        follow = self.find_for_user(incident_id, user_id)
        if follow is None:
            follow = IncidentFollow(
                incident_id=incident_id,
                user_id=user_id,
            )
            db.session.add(follow)

        follow.in_app_enabled = in_app_enabled
        follow.email_enabled = email_enabled
        follow.push_subscription_id = push_subscription_id
        db.session.flush()
        return follow

    def delete(self, follow: IncidentFollow) -> None:
        db.session.delete(follow)
