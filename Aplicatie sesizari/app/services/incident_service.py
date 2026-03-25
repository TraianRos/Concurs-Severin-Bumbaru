from app.extensions import db
from app.models.entities import INCIDENT_PRIORITY_CHOICES, INCIDENT_STATUS_CHOICES
from app.repositories.category_repository import CategoryRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository


class IncidentService:
    def __init__(
        self,
        incident_repository: IncidentRepository,
        category_repository: CategoryRepository,
        department_repository: DepartmentRepository,
        user_repository: UserRepository,
        notification_repository: NotificationRepository,
    ) -> None:
        self.incident_repository = incident_repository
        self.category_repository = category_repository
        self.department_repository = department_repository
        self.user_repository = user_repository
        self.notification_repository = notification_repository

    def homepage_data(self) -> dict:
        return {
            "status_counts": self.incident_repository.counts_by_status(),
            "recent_incidents": self.incident_repository.recent(limit=6),
            "department_count": self.department_repository.count(),
            "category_count": self.category_repository.count(),
        }

    def filter_options(self) -> dict:
        return {
            "categories": self.category_repository.all(),
            "departments": self.department_repository.all(),
            "priority_choices": INCIDENT_PRIORITY_CHOICES,
            "status_choices": INCIDENT_STATUS_CHOICES,
        }

    def list_incidents(self, filters: dict) -> list:
        return self.incident_repository.list_filtered(filters)

    def marker_payload(self, filters: dict) -> list[dict]:
        incidents = self.incident_repository.list_markers(filters)
        return [
            {
                "id": incident.id,
                "title": incident.title,
                "status": incident.status_label,
                "priority": incident.priority_label,
                "category": incident.category.name,
                "department": incident.assigned_department.name,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "address": incident.address,
                "url": f"/incidents/{incident.id}",
            }
            for incident in incidents
        ]

    def get_incident(self, incident_id: int):
        return self.incident_repository.find(incident_id)

    def create_incident(self, payload: dict, current_user) -> dict:
        title = payload.get("title", "").strip()
        description = payload.get("description", "").strip()
        address = payload.get("address", "").strip()
        category_id = payload.get("category_id", "").strip()
        priority = payload.get("priority", "").strip()
        latitude_raw = payload.get("latitude", "").strip()
        longitude_raw = payload.get("longitude", "").strip()

        if not title or not description or not address or not category_id or not priority:
            return {"ok": False, "message": "Completeaza toate campurile formularului."}
        if priority not in {value for value, _ in INCIDENT_PRIORITY_CHOICES}:
            return {"ok": False, "message": "Prioritatea selectata nu este valida."}
        if not category_id.isdigit():
            return {"ok": False, "message": "Categoria selectata nu este valida."}

        try:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
        except ValueError:
            return {"ok": False, "message": "Alege un punct pe harta pentru sesizare."}

        category = self.category_repository.find(int(category_id))
        if category is None:
            return {"ok": False, "message": "Categoria selectata nu exista."}

        # Departamentul initial vine automat din categorie, ca sa existe o prima redirectare coerenta.
        incident = self.incident_repository.create(
            title=title,
            description=description,
            address=address,
            latitude=latitude,
            longitude=longitude,
            priority=priority,
            status="noua",
            created_by_id=current_user.id,
            category_id=category.id,
            assigned_department_id=category.default_department_id,
        )

        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=current_user.id,
            message="Sesizarea a fost trimisa si asteapta analiza operatorului.",
            new_status="noua",
            new_department_id=category.default_department_id,
        )

        staff = self.user_repository.staff_for_department(category.default_department_id)
        if staff:
            self.notification_repository.create_many(
                [user.id for user in staff],
                incident.id,
                f"Sesizare noua: {incident.title}",
            )

        # Facem commit o singura data ca sa salvam impreuna sesizarea, istoricul si notificarile.
        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost trimisa cu succes.", "incident": incident}

    def operator_dashboard(self, user) -> dict:
        return {
            "queue": self.incident_repository.queue_for_operator(user.department_id),
            "departments": self.department_repository.all(),
        }

    def update_incident(self, incident_id: int, payload: dict, operator) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost gasita."}

        status = payload.get("status", "").strip()
        department_id_raw = payload.get("assigned_department_id", "").strip()
        message = payload.get("message", "").strip()

        valid_statuses = {value for value, _ in INCIDENT_STATUS_CHOICES}
        if status not in valid_statuses:
            return {"ok": False, "message": "Statusul selectat nu este valid."}
        if not department_id_raw.isdigit():
            return {"ok": False, "message": "Departamentul selectat nu este valid."}

        department = self.department_repository.find(int(department_id_raw))
        if department is None:
            return {"ok": False, "message": "Departamentul nu exista."}

        old_status = incident.status
        old_department_id = incident.assigned_department_id

        changed_status = old_status != status
        changed_department = old_department_id != department.id

        if not message and not changed_status and not changed_department:
            return {"ok": False, "message": "Nu exista nicio modificare de salvat."}

        incident.status = status
        incident.assigned_department_id = department.id

        if not message:
            message = "Operatorul a actualizat sesizarea."

        # Istoricul pastreaza atat mesajul uman, cat si schimbarea de status/departament.
        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=operator.id,
            message=message,
            old_status=old_status,
            new_status=status,
            old_department_id=old_department_id,
            new_department_id=department.id,
        )

        recipients = [incident.created_by_id]
        if changed_department:
            recipients.extend(user.id for user in self.user_repository.staff_for_department(department.id))

        self.notification_repository.create_many(
            recipients,
            incident.id,
            f'Sesizarea "{incident.title}" are acum statusul "{incident.status_label}".',
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost actualizata."}

    def notifications_for(self, user_id: int):
        return self.notification_repository.list_for_user(user_id)

    def unread_notifications(self, user_id: int) -> int:
        return self.notification_repository.unread_count(user_id)

    def mark_all_notifications_as_read(self, user_id: int) -> int:
        count = self.notification_repository.mark_all_as_read(user_id)
        db.session.commit()
        return count

    def admin_dashboard_data(self) -> dict:
        return {
            "departments": self.department_repository.all(),
            "categories": self.category_repository.all(),
            "operators": self.user_repository.list_operators(),
            "users": self.user_repository.all(),
        }

    def create_department(self, payload: dict) -> dict:
        name = payload.get("name", "").strip()
        description = payload.get("description", "").strip()
        contact_email = payload.get("contact_email", "").strip().lower()

        if not name or not description or not contact_email:
            return {"ok": False, "message": "Completeaza toate campurile departamentului."}
        if self.department_repository.find_by_name(name):
            return {"ok": False, "message": "Exista deja un departament cu acest nume."}

        self.department_repository.create(name, description, contact_email)
        db.session.commit()
        return {"ok": True, "message": "Departamentul a fost creat."}

    def create_category(self, payload: dict) -> dict:
        name = payload.get("name", "").strip()
        description = payload.get("description", "").strip()
        department_id_raw = payload.get("default_department_id", "").strip()

        if not name or not description or not department_id_raw:
            return {"ok": False, "message": "Completeaza toate campurile categoriei."}
        if self.category_repository.find_by_name(name):
            return {"ok": False, "message": "Exista deja o categorie cu acest nume."}
        if not department_id_raw.isdigit():
            return {"ok": False, "message": "Departamentul pentru categorie nu este valid."}

        department = self.department_repository.find(int(department_id_raw))
        if department is None:
            return {"ok": False, "message": "Departamentul selectat nu exista."}

        self.category_repository.create(name, description, department.id)
        db.session.commit()
        return {"ok": True, "message": "Categoria a fost creata."}
