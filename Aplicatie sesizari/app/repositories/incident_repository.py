from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.entities import Incident, IncidentUpdate


class IncidentRepository:
    def _base_query(self):
        return Incident.query.options(
            joinedload(Incident.creator),
            joinedload(Incident.category),
            joinedload(Incident.assigned_department),
            joinedload(Incident.updates).joinedload(IncidentUpdate.author),
        )

    def _apply_filters(self, query, filters: dict):
        search = filters.get("search", "").strip()
        status = filters.get("status", "").strip()
        priority = filters.get("priority", "").strip()
        category_id = filters.get("category_id", "").strip()
        department_id = filters.get("department_id", "").strip()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Incident.title.ilike(pattern),
                    Incident.description.ilike(pattern),
                    Incident.address.ilike(pattern),
                )
            )
        if status:
            query = query.filter(Incident.status == status)
        if priority:
            query = query.filter(Incident.priority == priority)
        if category_id.isdigit():
            query = query.filter(Incident.category_id == int(category_id))
        if department_id.isdigit():
            query = query.filter(Incident.assigned_department_id == int(department_id))

        return query

    def list_filtered(self, filters: dict) -> list[Incident]:
        query = self._apply_filters(self._base_query(), filters)
        return query.order_by(Incident.created_at.desc()).all()

    def list_markers(self, filters: dict) -> list[Incident]:
        query = self._apply_filters(self._base_query(), filters)
        return query.order_by(Incident.created_at.desc()).all()

    def find(self, incident_id: int) -> Incident | None:
        return self._base_query().filter(Incident.id == incident_id).first()

    def create(
        self,
        *,
        title: str,
        description: str,
        address: str,
        latitude: float,
        longitude: float,
        priority: str,
        status: str,
        created_by_id: int,
        category_id: int,
        assigned_department_id: int,
    ) -> Incident:
        incident = Incident(
            title=title,
            description=description,
            address=address,
            latitude=latitude,
            longitude=longitude,
            priority=priority,
            status=status,
            created_by_id=created_by_id,
            category_id=category_id,
            assigned_department_id=assigned_department_id,
        )
        db.session.add(incident)
        db.session.flush()
        return incident

    def create_update(
        self,
        *,
        incident_id: int,
        author_id: int,
        message: str,
        old_status: str | None = None,
        new_status: str | None = None,
        old_department_id: int | None = None,
        new_department_id: int | None = None,
    ) -> IncidentUpdate:
        update = IncidentUpdate(
            incident_id=incident_id,
            author_id=author_id,
            message=message,
            old_status=old_status,
            new_status=new_status,
            old_department_id=old_department_id,
            new_department_id=new_department_id,
        )
        db.session.add(update)
        db.session.flush()
        return update

    def counts_by_status(self) -> dict[str, int]:
        counts = {status: 0 for status in ["noua", "in_verificare", "redirectionata", "in_lucru", "rezolvata", "respinsa"]}
        for status, total in db.session.query(Incident.status, db.func.count(Incident.id)).group_by(Incident.status).all():
            counts[status] = total
        return counts

    def recent(self, limit: int = 5) -> list[Incident]:
        return self._base_query().order_by(Incident.created_at.desc()).limit(limit).all()

    def queue_for_operator(self, department_id: int | None) -> list[Incident]:
        query = self._base_query().filter(Incident.status.notin_(["rezolvata", "respinsa"]))
        if department_id is not None:
            query = query.filter(
                (Incident.assigned_department_id == department_id) | (Incident.status == "noua")
            )
        return query.order_by(Incident.updated_at.desc()).all()
