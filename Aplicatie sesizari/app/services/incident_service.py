from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models.entities import INCIDENT_PRIORITY_CHOICES, INCIDENT_STATUS_CHOICES, STATUS_LABELS
from app.repositories.category_repository import CategoryRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.incident_photo_repository import IncidentPhotoRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository

JPEG_ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}
JPEG_ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/pjpeg"}
JPEG_SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
OPERATOR_MANAGED_STATUSES = {"noua", "in_verificare", "in_lucru", "rezolvata", "respinsa"}


@dataclass
class PreparedPhotoUpload:
    original_name: str
    mime_type: str
    size_bytes: int
    width: int
    height: int
    content: bytes


def extract_jpeg_dimensions(content: bytes) -> tuple[int, int] | None:
    if len(content) < 4 or content[:2] != b"\xff\xd8":
        return None

    offset = 2
    content_length = len(content)

    while offset < content_length:
        while offset < content_length and content[offset] != 0xFF:
            offset += 1

        if offset >= content_length:
            return None

        while offset < content_length and content[offset] == 0xFF:
            offset += 1

        if offset >= content_length:
            return None

        marker = content[offset]
        offset += 1

        if marker == 0xD9:
            return None
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > content_length:
            return None

        segment_length = int.from_bytes(content[offset:offset + 2], "big")
        if segment_length < 2 or offset + segment_length > content_length:
            return None

        if marker in JPEG_SOF_MARKERS:
            if segment_length < 7:
                return None

            height = int.from_bytes(content[offset + 3:offset + 5], "big")
            width = int.from_bytes(content[offset + 5:offset + 7], "big")
            if width <= 0 or height <= 0:
                return None
            return width, height

        offset += segment_length

    return None


class IncidentService:
    def __init__(
        self,
        incident_repository: IncidentRepository,
        category_repository: CategoryRepository,
        department_repository: DepartmentRepository,
        user_repository: UserRepository,
        notification_repository: NotificationRepository,
        incident_photo_repository: IncidentPhotoRepository,
    ) -> None:
        self.incident_repository = incident_repository
        self.category_repository = category_repository
        self.department_repository = department_repository
        self.user_repository = user_repository
        self.notification_repository = notification_repository
        self.incident_photo_repository = incident_photo_repository

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

    def photo_form_options(self) -> dict:
        return {
            "max_files": current_app.config["PHOTO_MAX_FILES"],
            "max_size_bytes": current_app.config["PHOTO_MAX_FILE_SIZE_BYTES"],
            "processing_status_ready": current_app.config["PHOTO_PROCESSING_STATUS_READY"],
            "accept": ".jpg,.jpeg,.png,.webp",
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
                "department": incident.display_department_label,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "address": incident.address,
                "url": f"/incidents/{incident.id}",
            }
            for incident in incidents
        ]

    def get_incident(self, incident_id: int):
        return self.incident_repository.find(incident_id)

    def incident_detail_context(self, incident_id: int, viewer) -> dict | None:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return None

        return {
            "incident": incident,
            "timeline_entries": self._timeline_entries(viewer, incident),
            "visible_photos": self._visible_photos(viewer, incident),
            "can_view_reporter_identity": self._can_view_reporter_identity(viewer, incident),
            "can_view_internal": self._can_view_internal(viewer, incident),
            "can_dispatch_incident": self._can_dispatch_incident(viewer),
            "can_update_status": self._can_update_status(viewer, incident),
            "can_mark_irrelevant": self._can_mark_irrelevant(viewer, incident),
            "can_manage_photo_pertinence": self._can_dispatch_incident(viewer) and bool(incident.photos),
            "operator_status_choices": [
                (value, label) for value, label in INCIDENT_STATUS_CHOICES if value in OPERATOR_MANAGED_STATUSES
            ],
            "departments": self.department_repository.all(),
        }

    def can_view_incident_photos(self, viewer, incident) -> bool:
        return bool(self._visible_photos(viewer, incident))

    def get_incident_photo(self, incident_id: int, photo_id: int, viewer):
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return None

        photo = self.incident_photo_repository.find_for_incident(photo_id, incident_id)
        if photo is None:
            return None

        allowed_photo_ids = {visible_photo.id for visible_photo in self._visible_photos(viewer, incident)}
        if photo.id not in allowed_photo_ids:
            return None

        return photo

    def photo_storage_path(self, incident_id: int, stored_name: str) -> Path:
        return self._photo_directory(incident_id) / stored_name

    def create_incident(self, payload: dict, files, current_user) -> dict:
        title = payload.get("title", "").strip()
        description = payload.get("description", "").strip()
        address = payload.get("address", "").strip()
        category_id = payload.get("category_id", "").strip()
        priority = payload.get("priority", "").strip()
        latitude_raw = payload.get("latitude", "").strip()
        longitude_raw = payload.get("longitude", "").strip()
        photo_processing_status = payload.get("photo_processing_status", "").strip()
        suggested_department_id_raw = payload.get("suggested_department_id", "").strip()

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

        suggested_department_id = None
        if suggested_department_id_raw:
            if not suggested_department_id_raw.isdigit():
                return {"ok": False, "message": "Departamentul sugerat nu este valid."}
            suggested_department = self.department_repository.find(int(suggested_department_id_raw))
            if suggested_department is None:
                return {"ok": False, "message": "Departamentul sugerat nu exista."}
            suggested_department_id = suggested_department.id

        prepared_photos, photo_error = self._validate_uploaded_photos(files, photo_processing_status)
        if photo_error:
            return {"ok": False, "message": photo_error}

        saved_paths: list[Path] = []
        incident = None

        try:
            incident = self.incident_repository.create(
                title=title,
                description=description,
                address=address,
                latitude=latitude,
                longitude=longitude,
                priority=priority,
                status="in_triere",
                created_by_id=current_user.id,
                category_id=category.id,
                suggested_department_id=suggested_department_id,
                assigned_department_id=None,
            )

            self.incident_repository.create_update(
                incident_id=incident.id,
                author_id=current_user.id,
                message="Sesizarea a fost trimisa si asteapta trierea initiala.",
                new_status="in_triere",
            )

            triage_staff = self.user_repository.triage_staff()
            if triage_staff:
                self.notification_repository.create_many(
                    [user.id for user in triage_staff],
                    incident.id,
                    f"Sesizare noua in triere: {incident.title}",
                )

            saved_paths = self._store_photo_uploads(incident.id, prepared_photos)
            db.session.commit()
        except (OSError, SQLAlchemyError):
            db.session.rollback()
            self._cleanup_saved_photo_files(saved_paths, incident.id if incident is not None else None)
            return {
                "ok": False,
                "message": "Fotografiile nu au putut fi salvate. Incearca din nou.",
            }

        return {"ok": True, "message": "Sesizarea a fost trimisa cu succes.", "incident": incident}

    def operator_dashboard(self, user) -> dict:
        return {
            "queue": self.incident_repository.queue_for_operator(user.department_id),
            "departments": self.department_repository.all(),
        }

    def dispatcher_dashboard(self) -> dict:
        return {
            "queue": self.incident_repository.queue_for_dispatcher(),
            "departments": self.department_repository.all(),
        }

    def update_incident(self, incident_id: int, payload, operator) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost gasita."}

        action = payload.get("action", "set_status").strip()
        if action == "assign_department":
            return self._assign_department(incident, payload, operator)
        if action == "reject_suggestion":
            return self._reject_suggested_department(incident, payload, operator)
        if action == "reject_incident":
            return self._reject_incident(incident, payload, operator)
        if action == "mark_irrelevant":
            return self._mark_irrelevant_for_department(incident, payload, operator)
        if action == "set_status":
            return self._update_operational_status(incident, payload, operator)

        return {"ok": False, "message": "Actiunea solicitata nu este valida."}

    def update_photo_pertinence(self, incident_id: int, payload, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost gasita."}
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la configurarea fotografiilor."}
        if not incident.photos:
            return {"ok": False, "message": "Sesizarea nu are fotografii."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea selectiei fotografiilor este obligatorie."}

        selected_raw_ids = payload.getlist("pertinent_photo_ids") if hasattr(payload, "getlist") else []
        valid_photo_ids = {photo.id for photo in incident.photos}
        selected_photo_ids: set[int] = set()

        for raw_id in selected_raw_ids:
            if not raw_id.isdigit():
                return {"ok": False, "message": "Lista de fotografii pertinente nu este valida."}
            photo_id = int(raw_id)
            if photo_id not in valid_photo_ids:
                return {"ok": False, "message": "Una dintre fotografiile selectate nu apartine sesizarii."}
            selected_photo_ids.add(photo_id)

        current_selection = {photo.id for photo in incident.photos if photo.is_pertinent}
        if current_selection == selected_photo_ids:
            return {"ok": False, "message": "Nu exista modificari pentru lista fotografiilor pertinente."}

        for photo in incident.photos:
            photo.is_pertinent = photo.id in selected_photo_ids

        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
        )
        db.session.commit()
        return {"ok": True, "message": "Selectia fotografiilor pertinente a fost actualizata."}

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

        if not name or not description:
            return {"ok": False, "message": "Completeaza toate campurile categoriei."}
        if self.category_repository.find_by_name(name):
            return {"ok": False, "message": "Exista deja o categorie cu acest nume."}

        default_department_id = None
        if department_id_raw:
            if not department_id_raw.isdigit():
                return {"ok": False, "message": "Departamentul pentru categorie nu este valid."}

            department = self.department_repository.find(int(department_id_raw))
            if department is None:
                return {"ok": False, "message": "Departamentul selectat nu exista."}
            default_department_id = department.id

        self.category_repository.create(name, description, default_department_id)
        db.session.commit()
        return {"ok": True, "message": "Categoria a fost creata."}

    def _assign_department(self, incident, payload, actor) -> dict:
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la trierea sesizarilor."}

        department_id_raw = payload.get("assigned_department_id", "").strip()
        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea atribuirii este obligatorie."}
        if not department_id_raw.isdigit():
            return {"ok": False, "message": "Departamentul selectat nu este valid."}

        department = self.department_repository.find(int(department_id_raw))
        if department is None:
            return {"ok": False, "message": "Departamentul nu exista."}

        if incident.status != "in_triere" and incident.assigned_department_id == department.id:
            return {"ok": False, "message": "Sesizarea este deja atribuita acestui departament."}

        old_status = incident.status
        old_department_id = incident.assigned_department_id if incident.status != "in_triere" else None
        incident.assigned_department_id = department.id
        incident.suggested_department_id = None
        incident.status = "noua" if old_status == "in_triere" else "redirectionata"

        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
            old_status=old_status,
            new_status=incident.status,
            old_department_id=old_department_id,
            new_department_id=department.id,
        )

        recipients = [incident.created_by_id]
        recipients.extend(user.id for user in self.user_repository.staff_for_department(department.id))
        self.notification_repository.create_many(
            recipients,
            incident.id,
            f'Sesizarea "{incident.title}" a fost atribuita departamentului "{department.name}".',
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost atribuita departamentului selectat."}

    def _reject_suggested_department(self, incident, payload, actor) -> dict:
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la trierea sesizarilor."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea respingerii sugestiei este obligatorie."}
        if incident.suggested_department_id is None:
            return {"ok": False, "message": "Sesizarea nu are un departament sugerat de respins."}

        old_suggested_department_id = incident.suggested_department_id
        incident.suggested_department_id = None
        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
            old_status=incident.status,
            new_status=incident.status,
            old_department_id=old_suggested_department_id,
            new_department_id=None,
        )
        self.notification_repository.create_many(
            [incident.created_by_id],
            incident.id,
            f'Sugestia initiala de departament pentru sesizarea "{incident.title}" a fost retrimisa la triere.',
        )

        db.session.commit()
        return {"ok": True, "message": "Sugestia de departament a fost respinsa si cazul ramane in triere."}

    def _reject_incident(self, incident, payload, actor) -> dict:
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la trierea sesizarilor."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea respingerii este obligatorie."}
        if incident.status == "respinsa":
            return {"ok": False, "message": "Sesizarea este deja respinsa."}

        old_status = incident.status
        incident.status = "respinsa"
        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
            old_status=old_status,
            new_status="respinsa",
            old_department_id=incident.assigned_department_id if old_status != "in_triere" else None,
        )
        self.notification_repository.create_many(
            [incident.created_by_id],
            incident.id,
            f'Sesizarea "{incident.title}" a fost respinsa.',
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost respinsa."}

    def _mark_irrelevant_for_department(self, incident, payload, actor) -> dict:
        if not self._can_mark_irrelevant(actor, incident):
            return {"ok": False, "message": "Nu poti retrimite aceasta sesizare la triere."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea retrimiterii la triere este obligatorie."}
        if incident.status == "in_triere":
            return {"ok": False, "message": "Sesizarea este deja in triere."}

        old_status = incident.status
        old_department_id = incident.assigned_department_id
        incident.status = "in_triere"
        incident.suggested_department_id = None
        incident.assigned_department_id = None

        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
            old_status=old_status,
            new_status="in_triere",
            old_department_id=old_department_id,
            new_department_id=None,
        )

        recipients = [incident.created_by_id]
        recipients.extend(user.id for user in self.user_repository.triage_staff())
        self.notification_repository.create_many(
            recipients,
            incident.id,
            f'Sesizarea "{incident.title}" a fost retrimisa spre triere.',
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost retrimisa spre triere."}

    def _update_operational_status(self, incident, payload, actor) -> dict:
        if not self._can_update_status(actor, incident):
            return {"ok": False, "message": "Nu ai acces la gestionarea acestei sesizari."}

        status = payload.get("status", "").strip()
        message = payload.get("message", "").strip()
        if status not in OPERATOR_MANAGED_STATUSES:
            return {"ok": False, "message": "Statusul selectat nu este valid."}
        if incident.status == "in_triere":
            return {"ok": False, "message": "Sesizarea trebuie triata inainte de gestionarea operationala."}
        if status == incident.status and not message:
            return {"ok": False, "message": "Nu exista nicio modificare de salvat."}

        old_status = incident.status
        incident.status = status

        if not message:
            message = "Operatorul a actualizat sesizarea."

        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
            old_status=old_status,
            new_status=status,
            old_department_id=incident.assigned_department_id,
            new_department_id=incident.assigned_department_id,
        )

        self.notification_repository.create_many(
            [incident.created_by_id],
            incident.id,
            f'Sesizarea "{incident.title}" are acum statusul "{incident.status_label}".',
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost actualizata."}

    def _can_dispatch_incident(self, viewer) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and getattr(viewer, "role", None) in ["dispatcher", "admin"]
        )

    def _can_operate_incident(self, viewer, incident) -> bool:
        if not getattr(viewer, "is_authenticated", False):
            return False
        if getattr(viewer, "role", None) == "admin":
            return True
        return bool(
            viewer.role == "operator"
            and viewer.department_id is not None
            and incident.status != "in_triere"
            and incident.assigned_department_id == viewer.department_id
        )

    def _can_view_internal(self, viewer, incident) -> bool:
        return self._can_dispatch_incident(viewer) or self._can_operate_incident(viewer, incident)

    def _can_view_reporter_identity(self, viewer, incident) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and (viewer.id == incident.created_by_id or self._can_view_internal(viewer, incident))
        )

    def _can_update_status(self, viewer, incident) -> bool:
        return incident.status != "in_triere" and self._can_operate_incident(viewer, incident)

    def _can_mark_irrelevant(self, viewer, incident) -> bool:
        return incident.status != "in_triere" and self._can_operate_incident(viewer, incident)

    def _visible_photos(self, viewer, incident) -> list:
        if not getattr(viewer, "is_authenticated", False):
            return []
        if viewer.id == incident.created_by_id or self._can_dispatch_incident(viewer):
            return list(incident.photos)
        if self._can_operate_incident(viewer, incident):
            return [photo for photo in incident.photos if photo.is_pertinent]
        return []

    def _timeline_entries(self, viewer, incident) -> list[dict]:
        if self._can_view_internal(viewer, incident):
            return self._internal_timeline_entries(incident)
        return self._public_timeline_entries(incident)

    def _internal_timeline_entries(self, incident) -> list[dict]:
        departments = self._department_lookup_for_incident(incident)
        entries = []
        for update in incident.updates:
            entries.append(
                {
                    "created_at": update.created_at,
                    "author_name": update.author.full_name,
                    "message": update.message,
                    "status_from": STATUS_LABELS.get(update.old_status, update.old_status) if update.old_status else None,
                    "status_to": STATUS_LABELS.get(update.new_status, update.new_status) if update.new_status else None,
                    "department_from": departments.get(update.old_department_id),
                    "department_to": departments.get(update.new_department_id),
                }
            )
        return entries

    def _public_timeline_entries(self, incident) -> list[dict]:
        departments = self._department_lookup_for_incident(incident)
        entries = []
        for update in incident.updates:
            message = self._public_message_for_update(update, departments)
            if message is None:
                continue

            entries.append(
                {
                    "created_at": update.created_at,
                    "author_name": "Platforma",
                    "message": message,
                    "status_from": None,
                    "status_to": None,
                    "department_from": None,
                    "department_to": None,
                }
            )
        return entries

    def _public_message_for_update(self, update, departments: dict[int, str]) -> str | None:
        if update.new_status == "in_triere" and update.old_status is None:
            return "Sesizarea a fost inregistrata si asteapta trierea initiala."
        if update.new_status == "in_triere" and update.old_status is not None:
            return "Sesizarea a fost retrimisa spre triere."
        if update.old_department_id is not None and update.new_department_id is None and update.new_status == update.old_status:
            return "Sugestia initiala de departament a fost retrimisa la triere."
        if update.new_department_id is not None and update.old_department_id != update.new_department_id:
            department_name = departments.get(update.new_department_id, "departamentul selectat")
            return f'Sesizarea a fost directionata catre departamentul "{department_name}".'
        if update.new_status and update.old_status != update.new_status:
            return f'Sesizarea are acum statusul "{STATUS_LABELS.get(update.new_status, update.new_status)}".'
        return None

    def _department_lookup_for_incident(self, incident) -> dict[int, str]:
        departments = {}

        if incident.assigned_department is not None:
            departments[incident.assigned_department.id] = incident.assigned_department.name
        if incident.suggested_department is not None:
            departments[incident.suggested_department.id] = incident.suggested_department.name

        for update in incident.updates:
            for department_id in [update.old_department_id, update.new_department_id]:
                if department_id is None or department_id in departments:
                    continue
                department = self.department_repository.find(department_id)
                if department is not None:
                    departments[department_id] = department.name

        return departments

    def _normalize_photo_files(self, files) -> list[FileStorage]:
        if files is None or not hasattr(files, "getlist"):
            return []

        return [
            file_storage
            for file_storage in files.getlist("photos")
            if file_storage and file_storage.filename and file_storage.filename.strip()
        ]

    def _validate_uploaded_photos(
        self,
        files,
        photo_processing_status: str,
    ) -> tuple[list[PreparedPhotoUpload], str | None]:
        uploads = self._normalize_photo_files(files)
        if not uploads:
            return [], None

        if len(uploads) > current_app.config["PHOTO_MAX_FILES"]:
            return [], f'Poti incarca maximum {current_app.config["PHOTO_MAX_FILES"]} fotografii.'

        if photo_processing_status != current_app.config["PHOTO_PROCESSING_STATUS_READY"]:
            return [], "Browserul nu a finalizat procesarea fotografiilor. Incearca din nou."

        prepared_uploads: list[PreparedPhotoUpload] = []
        max_size = current_app.config["PHOTO_MAX_FILE_SIZE_BYTES"]

        for upload in uploads:
            original_name = self._clean_photo_name(upload.filename)
            extension = Path(original_name).suffix.lower()
            if extension not in JPEG_ALLOWED_EXTENSIONS:
                return [], "Serverul accepta doar fotografii JPEG procesate in frontend."

            mime_type = (upload.mimetype or "").lower()
            if mime_type not in JPEG_ALLOWED_MIME_TYPES:
                return [], "Tipul fotografiei incarcate nu este valid."

            content = upload.read()
            upload.stream.seek(0)

            if not content:
                return [], "Una dintre fotografii este goala."
            if len(content) > max_size:
                return [], "Una dintre fotografii depaseste limita de 5 MB dupa compresie."
            if not content.startswith(b"\xff\xd8") or not content.endswith(b"\xff\xd9"):
                return [], "Una dintre fotografii nu are o semnatura JPEG valida."

            dimensions = extract_jpeg_dimensions(content)
            if dimensions is None:
                return [], "Una dintre fotografii nu are o structura JPEG valida."

            width, height = dimensions
            prepared_uploads.append(
                PreparedPhotoUpload(
                    original_name=original_name,
                    mime_type="image/jpeg",
                    size_bytes=len(content),
                    width=width,
                    height=height,
                    content=content,
                )
            )

        return prepared_uploads, None

    def _clean_photo_name(self, filename: str) -> str:
        cleaned_name = Path(filename).name.strip()
        if not cleaned_name:
            return "fotografie.jpg"
        if len(cleaned_name) > 255:
            suffix = Path(cleaned_name).suffix
            stem = Path(cleaned_name).stem[: max(1, 255 - len(suffix))]
            return f"{stem}{suffix}"
        return cleaned_name

    def _store_photo_uploads(self, incident_id: int, uploads: list[PreparedPhotoUpload]) -> list[Path]:
        if not uploads:
            return []

        photo_directory = self._photo_directory(incident_id)
        photo_directory.mkdir(parents=True, exist_ok=True)

        saved_paths: list[Path] = []
        for upload in uploads:
            stored_name = f"{uuid4().hex}.jpg"
            file_path = photo_directory / stored_name
            file_path.write_bytes(upload.content)
            saved_paths.append(file_path)

            self.incident_photo_repository.create(
                incident_id=incident_id,
                stored_name=stored_name,
                original_name=upload.original_name,
                mime_type=upload.mime_type,
                size_bytes=upload.size_bytes,
                width=upload.width,
                height=upload.height,
            )

        return saved_paths

    def _cleanup_saved_photo_files(self, saved_paths: list[Path], incident_id: int | None) -> None:
        for file_path in saved_paths:
            file_path.unlink(missing_ok=True)

        if incident_id is None:
            return

        photo_directory = self._photo_directory(incident_id)
        try:
            photo_directory.rmdir()
        except OSError:
            pass

    def _photo_directory(self, incident_id: int) -> Path:
        return Path(current_app.instance_path) / current_app.config["PHOTO_UPLOAD_SUBDIR"] / str(incident_id)
