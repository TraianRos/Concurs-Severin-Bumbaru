from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.models.entities import Incident, IncidentFollow, IncidentReport, IncidentUpdate

MAP_HIDDEN_STATUSES = ["rezolvata", "respinsa"]
VISIBLE_INCIDENT_STATE = "visible"


class IncidentRepository:
    def _base_query(self):
        return Incident.query.options(
            joinedload(Incident.creator),
            joinedload(Incident.category),
            joinedload(Incident.suggested_department),
            joinedload(Incident.assigned_department),
            selectinload(Incident.photos),
            selectinload(Incident.updates).joinedload(IncidentUpdate.author),
            selectinload(Incident.votes),
            selectinload(Incident.reports).joinedload(IncidentReport.reporter),
            selectinload(Incident.reports).joinedload(IncidentReport.reviewer),
            selectinload(Incident.follows).joinedload(IncidentFollow.user),
            selectinload(Incident.follows).joinedload(IncidentFollow.push_subscription),
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

    def _apply_visibility_filter(self, query, *, include_hidden: bool):
        if include_hidden:
            return query
        return query.filter(Incident.visibility_state == VISIBLE_INCIDENT_STATE)

    def list_filtered(self, filters: dict, *, include_hidden: bool = False) -> list[Incident]:
        query = self._apply_filters(self._base_query(), filters)
        query = self._apply_visibility_filter(query, include_hidden=include_hidden)
        return query.order_by(Incident.created_at.desc()).all()

    def list_markers(self, filters: dict, *, include_hidden: bool = False) -> list[Incident]:
        query = self._apply_filters(self._base_query(), filters)
        query = self._apply_visibility_filter(query, include_hidden=include_hidden)
        query = query.filter(Incident.status.notin_(MAP_HIDDEN_STATUSES))
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
        suggested_department_id: int | None,
        assigned_department_id: int | None,
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
            suggested_department_id=suggested_department_id,
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

    def counts_by_status(self, *, include_hidden: bool = False) -> dict[str, int]:
        counts = {
            status: 0
            for status in [
                "in_triere",
                "noua",
                "in_verificare",
                "redirectionata",
                "in_lucru",
                "rezolvata",
                "respinsa",
            ]
        }
        query = db.session.query(Incident.status, db.func.count(Incident.id))
        query = self._apply_visibility_filter(query, include_hidden=include_hidden)
        for status, total in query.group_by(Incident.status).all():
            counts[status] = total
        return counts

    def recent(self, limit: int = 5, *, include_hidden: bool = False) -> list[Incident]:
        query = self._apply_visibility_filter(self._base_query(), include_hidden=include_hidden)
        return query.order_by(Incident.created_at.desc()).limit(limit).all()

    def queue_for_operator(self, department_id: int | None, *, include_hidden: bool = False) -> list[Incident]:
        if department_id is None:
            return []

        query = self._base_query().filter(
            Incident.status.notin_(["in_triere", "rezolvata", "respinsa"]),
            Incident.assigned_department_id == department_id,
        )
        query = self._apply_visibility_filter(query, include_hidden=include_hidden)
        return query.order_by(Incident.updated_at.desc()).all()

    def queue_for_dispatcher(self, *, include_hidden: bool = False) -> list[Incident]:
        return (
            self._apply_visibility_filter(self._base_query(), include_hidden=include_hidden)
            .filter(Incident.status == "in_triere")
            .order_by(Incident.updated_at.desc(), Incident.created_at.desc())
            .all()
        )

    def hidden_for_moderation(self) -> list[Incident]:
        return (
            self._base_query()
            .filter(Incident.visibility_state != VISIBLE_INCIDENT_STATE)
            .order_by(Incident.updated_at.desc(), Incident.created_at.desc())
            .all()
        )

    def delete(self, incident: Incident) -> None:
        db.session.delete(incident)
