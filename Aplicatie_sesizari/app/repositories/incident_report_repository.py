from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.entities import IncidentReport


class IncidentReportRepository:
    def _base_query(self):
        return IncidentReport.query.options(
            joinedload(IncidentReport.incident),
            joinedload(IncidentReport.reporter),
            joinedload(IncidentReport.reviewer),
        )

    def find(self, report_id: int) -> IncidentReport | None:
        return self._base_query().filter(IncidentReport.id == report_id).first()

    def find_open_for_user(self, incident_id: int, user_id: int) -> IncidentReport | None:
        return (
            self._base_query()
            .filter_by(incident_id=incident_id, reporter_id=user_id, status="deschis")
            .first()
        )

    def find_for_user(self, incident_id: int, user_id: int) -> IncidentReport | None:
        return (
            self._base_query()
            .filter_by(incident_id=incident_id, reporter_id=user_id)
            .first()
        )

    def list_open_for_incident(self, incident_id: int) -> list[IncidentReport]:
        return (
            self._base_query()
            .filter_by(incident_id=incident_id, status="deschis")
            .order_by(IncidentReport.created_at.desc())
            .all()
        )

    def list_open_for_moderation(self) -> list[IncidentReport]:
        return (
            self._base_query()
            .filter_by(status="deschis")
            .order_by(IncidentReport.created_at.desc())
            .all()
        )

    def count_open_distinct_reporters(self, incident_id: int) -> int:
        return (
            db.session.query(db.func.count(db.distinct(IncidentReport.reporter_id)))
            .filter_by(incident_id=incident_id, status="deschis")
            .scalar()
            or 0
        )

    def create(self, *, incident_id: int, reporter_id: int, reason: str, details: str) -> IncidentReport:
        report = IncidentReport(
            incident_id=incident_id,
            reporter_id=reporter_id,
            reason=reason,
            details=details,
        )
        db.session.add(report)
        db.session.flush()
        return report
