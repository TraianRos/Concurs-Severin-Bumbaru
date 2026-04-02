import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models.entities import (
    FOLLOW_CHANNEL_LABELS,
    INCIDENT_PRIORITY_CHOICES,
    INCIDENT_REPORT_REASON_CHOICES,
    INCIDENT_REPORT_REASON_LABELS,
    INCIDENT_STATUS_CHOICES,
    STATUS_LABELS,
    utc_now,
)
from app.repositories.category_repository import CategoryRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.incident_follow_repository import IncidentFollowRepository
from app.repositories.incident_photo_repository import IncidentPhotoRepository
from app.repositories.incident_report_repository import IncidentReportRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.incident_vote_repository import IncidentVoteRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.web_push_subscription_repository import WebPushSubscriptionRepository
from app.services.notification_dispatch_service import NotificationDispatchService

JPEG_ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}
JPEG_ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/pjpeg"}
JPEG_SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
OPERATOR_MANAGED_STATUSES = {"noua", "in_verificare", "in_lucru", "rezolvata", "respinsa"}
REPORT_REASON_VALUES = {value for value, _ in INCIDENT_REPORT_REASON_CHOICES}
FOLLOW_CHANNEL_VALUES = {"in_app", "email", "web_push"}
VISIBLE_INCIDENT_STATE = "visible"
AUTO_HIDDEN_INCIDENT_STATE = "auto_hidden"
CONFIRMED_HIDDEN_INCIDENT_STATE = "confirmed_hidden"
HIDDEN_INCIDENT_STATES = {AUTO_HIDDEN_INCIDENT_STATE, CONFIRMED_HIDDEN_INCIDENT_STATE}


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
        incident_vote_repository: IncidentVoteRepository,
        incident_report_repository: IncidentReportRepository,
        incident_follow_repository: IncidentFollowRepository,
        web_push_subscription_repository: WebPushSubscriptionRepository,
        notification_dispatch_service: NotificationDispatchService,
    ) -> None:
        self.incident_repository = incident_repository
        self.category_repository = category_repository
        self.department_repository = department_repository
        self.user_repository = user_repository
        self.notification_repository = notification_repository
        self.incident_photo_repository = incident_photo_repository
        self.incident_vote_repository = incident_vote_repository
        self.incident_report_repository = incident_report_repository
        self.incident_follow_repository = incident_follow_repository
        self.web_push_subscription_repository = web_push_subscription_repository
        self.notification_dispatch_service = notification_dispatch_service

    def _limit(self, key: str) -> int:
        return int(current_app.config.get("FORM_LIMITS", {}).get(key, 0))

    def homepage_data(self, viewer=None) -> dict:
        include_hidden = self._include_hidden_for_viewer(viewer)
        return {
            "status_counts": self.incident_repository.counts_by_status(include_hidden=include_hidden),
            "recent_incidents": self.incident_repository.recent(limit=6, include_hidden=include_hidden),
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

    def list_incidents(self, filters: dict, viewer=None) -> list:
        return self.incident_repository.list_filtered(
            filters,
            include_hidden=self._include_hidden_for_viewer(viewer),
        )

    def marker_payload(self, filters: dict, viewer=None) -> list[dict]:
        incidents = self.incident_repository.list_markers(
            filters,
            include_hidden=self._include_hidden_for_viewer(viewer),
        )
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
        if incident is None or not self._can_access_incident(viewer, incident):
            return None

        viewer_follow = None
        viewer_open_report = None
        has_voted = False

        if getattr(viewer, "is_authenticated", False):
            viewer_follow = self.incident_follow_repository.find_for_user(incident.id, viewer.id)
            viewer_open_report = self.incident_report_repository.find_open_for_user(incident.id, viewer.id)
            has_voted = self.incident_vote_repository.find_for_user(incident.id, viewer.id) is not None

        can_moderate_reports = self._can_moderate_reports(viewer)
        open_reports = self.incident_report_repository.list_open_for_incident(incident.id) if can_moderate_reports else []

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
            "visibility_state_label": incident.visibility_state_label,
            "vote_count": incident.vote_count,
            "has_voted": has_voted,
            "can_vote": self._can_vote(viewer, incident),
            "can_report": self._can_report(viewer, incident),
            "has_open_report": viewer_open_report is not None,
            "open_reports": open_reports,
            "can_moderate_reports": can_moderate_reports,
            "can_restore_visibility": self._can_restore_visibility(viewer, incident),
            "can_delete_incident": self._can_delete_incident(viewer),
            "report_reason_choices": INCIDENT_REPORT_REASON_CHOICES,
            "follow_channels": list(viewer_follow.active_channels) if viewer_follow else [],
            "follow_channel_labels": FOLLOW_CHANNEL_LABELS,
            "follow_push_subscription_id": (
                viewer_follow.push_subscription_id if viewer_follow and viewer_follow.web_push_enabled else None
            ),
            "can_follow": self._can_follow(viewer, incident),
            "report_moderation_state": {"open_count": len(open_reports)},
        }

    def can_view_incident_photos(self, viewer, incident) -> bool:
        return bool(self._visible_photos(viewer, incident))

    def get_incident_photo(self, incident_id: int, photo_id: int, viewer):
        incident = self.incident_repository.find(incident_id)
        if incident is None or not self._can_access_incident(viewer, incident):
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
            return {"ok": False, "message": "Completează toate câmpurile formularului."}
        if len(title) > self._limit("incident_title"):
            return {"ok": False, "message": "Titlul sesizării nu poate depăși 200 de caractere."}
        if len(address) > self._limit("incident_address"):
            return {"ok": False, "message": "Adresa sesizării nu poate depăși 255 de caractere."}
        if len(description) > self._limit("incident_description"):
            return {"ok": False, "message": "Descrierea sesizării nu poate depăși 2000 de caractere."}
        if priority not in {value for value, _ in INCIDENT_PRIORITY_CHOICES}:
            return {"ok": False, "message": "Prioritatea selectată nu este validă."}
        if not category_id.isdigit():
            return {"ok": False, "message": "Categoria selectată nu este validă."}

        try:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
        except ValueError:
            return {
                "ok": False,
                "message": "Folosește locația dispozitivului sau selectează un punct pe hartă pentru sesizare.",
            }

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return {"ok": False, "message": "Coordonatele introduse nu sunt valide."}

        category = self.category_repository.find(int(category_id))
        if category is None:
            return {"ok": False, "message": "Categoria selectată nu există."}

        suggested_department_id = None
        if suggested_department_id_raw:
            if not suggested_department_id_raw.isdigit():
                return {"ok": False, "message": "Departamentul sugerat nu este valid."}
            suggested_department = self.department_repository.find(int(suggested_department_id_raw))
            if suggested_department is None:
                return {"ok": False, "message": "Departamentul sugerat nu există."}
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
                message="Sesizarea a fost trimisă și așteaptă trierea inițială.",
                new_status="in_triere",
            )

            self.incident_follow_repository.create_or_update(
                incident_id=incident.id,
                user_id=current_user.id,
                in_app_enabled=True,
                email_enabled=False,
                push_subscription_id=None,
            )

            triage_staff = self.user_repository.triage_staff()
            if triage_staff:
                self.notification_dispatch_service.notify_direct_in_app(
                    [user.id for user in triage_staff],
                    incident,
                    f"Sesizare nouă în triere: {incident.title}",
                    exclude_user_ids={current_user.id},
                )

            saved_paths = self._store_photo_uploads(incident.id, prepared_photos)
            db.session.commit()
        except (OSError, SQLAlchemyError):
            db.session.rollback()
            self._cleanup_saved_photo_files(saved_paths, incident.id if incident is not None else None)
            return {"ok": False, "message": "Fotografiile nu au putut fi salvate. Încearcă din nou."}

        return {"ok": True, "message": "Sesizarea a fost trimisă cu succes.", "incident": incident}

    def toggle_vote(self, incident_id: int, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None or not self._can_access_incident(actor, incident):
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}
        if not self._can_vote(actor, incident):
            return {"ok": False, "message": "Nu îți poți vota propria sesizare."}

        existing_vote = self.incident_vote_repository.find_for_user(incident.id, actor.id)
        if existing_vote is None:
            self.incident_vote_repository.create(incident.id, actor.id)
            action_label = "Susținerea a fost înregistrată."
            voted = True
        else:
            self.incident_vote_repository.delete(existing_vote)
            action_label = "Susținerea a fost retrasă."
            voted = False

        db.session.commit()
        refreshed_incident = self.incident_repository.find(incident.id)
        return {
            "ok": True,
            "message": action_label,
            "voted": voted,
            "vote_count": refreshed_incident.vote_count if refreshed_incident is not None else 0,
        }

    def submit_report(self, incident_id: int, payload, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None or not self._can_access_incident(actor, incident):
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}
        if not self._can_report(actor, incident):
            return {"ok": False, "message": "Nu îți poți raporta propria sesizare."}

        reason = payload.get("reason", "").strip()
        details = payload.get("details", "").strip()

        if reason not in REPORT_REASON_VALUES:
            return {"ok": False, "message": "Motivul raportării nu este valid."}
        if not details:
            return {"ok": False, "message": "Detaliile raportării sunt obligatorii."}
        if len(details) > self._limit("incident_report_details"):
            return {"ok": False, "message": "Detaliile raportării nu pot depăși 1000 de caractere."}
        if self.incident_report_repository.find_for_user(incident.id, actor.id) is not None:
            return {"ok": False, "message": "Ai raportat deja această sesizare."}

        self.incident_report_repository.create(
            incident_id=incident.id,
            reporter_id=actor.id,
            reason=reason,
            details=details,
        )

        moderators = self.user_repository.triage_staff()
        self.notification_dispatch_service.notify_direct_in_app(
            [user.id for user in moderators],
            incident,
            f'Sesizarea "{incident.title}" a fost raportată pentru: {INCIDENT_REPORT_REASON_LABELS[reason]}.',
            exclude_user_ids={actor.id},
        )

        if self.incident_report_repository.count_open_distinct_reporters(incident.id) >= self._auto_hide_report_threshold():
            self._set_incident_visibility(
                incident,
                new_state=AUTO_HIDDEN_INCIDENT_STATE,
                author_id=actor.id,
                message=(
                    f"Sesizarea a fost ascunsă automat după atingerea pragului de "
                    f"{self._auto_hide_report_threshold()} raportări deschise."
                ),
            )

        db.session.commit()
        return {"ok": True, "message": "Raportarea a fost trimisă pentru moderare."}

    def update_follow_preferences(self, incident_id: int, payload, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None or not self._can_access_incident(actor, incident):
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}
        if not self._can_follow(actor, incident):
            return {"ok": False, "message": "Trebuie să fii autentificat pentru a urmări sesizări."}

        raw_channels = payload.getlist("channels") if hasattr(payload, "getlist") else payload.get("channels", [])
        if isinstance(raw_channels, str):
            raw_channels = [raw_channels]
        channels = {channel for channel in raw_channels if channel in FOLLOW_CHANNEL_VALUES}
        if len(channels) != len(set(raw_channels)):
            return {"ok": False, "message": "Canalele selectate pentru urmărire nu sunt valide."}

        push_subscription_id = None
        if "web_push" in channels:
            push_subscription_id_raw = payload.get("push_subscription_id", "").strip()
            if not push_subscription_id_raw.isdigit():
                return {"ok": False, "message": "Notificările pe dispozitiv trebuie activate din browserul curent."}

            subscription = self.web_push_subscription_repository.find(int(push_subscription_id_raw))
            if subscription is None or subscription.user_id != actor.id or not subscription.is_active:
                return {"ok": False, "message": "Dispozitivul selectat pentru notificări nu mai este disponibil."}
            push_subscription_id = subscription.id

        existing_follow = self.incident_follow_repository.find_for_user(incident.id, actor.id)
        if not channels:
            if existing_follow is not None:
                self.incident_follow_repository.delete(existing_follow)
                db.session.commit()
            return {"ok": True, "message": "Urmărirea sesizării a fost dezactivată."}

        follow = self.incident_follow_repository.create_or_update(
            incident_id=incident.id,
            user_id=actor.id,
            in_app_enabled="in_app" in channels,
            email_enabled="email" in channels,
            push_subscription_id=push_subscription_id,
        )
        db.session.commit()

        label_list = ", ".join(FOLLOW_CHANNEL_LABELS[channel] for channel in follow.active_channels)
        return {"ok": True, "message": f"Preferințele de urmărire au fost salvate: {label_list}."}

    def register_push_subscription(self, actor, payload: dict) -> dict:
        public_key = current_app.config.get("WEB_PUSH_PUBLIC_KEY", "").strip()
        private_key = current_app.config.get("WEB_PUSH_PRIVATE_KEY", "").strip()
        push_subject = current_app.config.get("WEB_PUSH_SUBJECT", "").strip()
        if not public_key or not private_key or not push_subject:
            return {"ok": False, "message": "Web Push nu este configurat pe server."}

        endpoint = str(payload.get("endpoint", "")).strip()
        keys = payload.get("keys") or {}
        p256dh_key = str(keys.get("p256dh", "")).strip()
        auth_key = str(keys.get("auth", "")).strip()

        if not endpoint or not p256dh_key or not auth_key:
            return {"ok": False, "message": "Abonarea dispozitivului este incompletă."}

        subscription = self.web_push_subscription_repository.create_or_update(
            user_id=actor.id,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
        )
        db.session.commit()
        return {"ok": True, "message": "Dispozitivul a fost pregătit pentru notificări.", "subscription": subscription}

    def review_report(self, report_id: int, payload, moderator) -> dict:
        report = self.incident_report_repository.find(report_id)
        if report is None:
            return {"ok": False, "message": "Raportul nu a fost găsit."}
        if not self._can_moderate_reports(moderator):
            return {"ok": False, "message": "Nu ai acces la moderarea rapoartelor."}
        if report.status != "deschis":
            return {"ok": False, "message": "Raportul a fost deja procesat."}

        action = payload.get("action", "").strip()
        resolution_note = payload.get("resolution_note", "").strip()
        if action not in {"confirm", "reject"}:
            return {"ok": False, "message": "Acțiunea de moderare nu este validă."}
        if not resolution_note:
            return {"ok": False, "message": "Nota de rezolvare este obligatorie."}

        report.status = "confirmat" if action == "confirm" else "respins"
        report.reviewer_id = moderator.id
        report.reviewed_at = utc_now()
        report.resolution_note = resolution_note

        if action == "confirm":
            self._set_incident_visibility(
                report.incident,
                new_state=CONFIRMED_HIDDEN_INCIDENT_STATE,
                author_id=moderator.id,
                message=resolution_note,
            )
        else:
            self._refresh_auto_hidden_visibility(
                report.incident,
                actor_id=moderator.id,
                restored_message=(
                    "Sesizarea a redevenit vizibilă după scăderea numărului de raportări deschise sub prag."
                ),
            )

        moderation_message = (
            f'Raportarea ta pentru sesizarea "{report.incident.title}" a fost confirmată.'
            if action == "confirm"
            else f'Raportarea ta pentru sesizarea "{report.incident.title}" a fost respinsă.'
        )
        self.notification_dispatch_service.notify_direct_in_app(
            [report.reporter_id],
            report.incident,
            moderation_message,
            exclude_user_ids={moderator.id},
        )

        db.session.commit()
        return {
            "ok": True,
            "message": "Raportul a fost procesat.",
            "incident_id": report.incident_id,
        }

    def restore_visibility(self, incident_id: int, payload, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}
        if not self._can_restore_visibility(actor, incident):
            return {"ok": False, "message": "Nu ai acces la restaurarea acestei sesizări."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea restaurării este obligatorie."}
        if incident.visibility_state == AUTO_HIDDEN_INCIDENT_STATE and incident.open_reporter_count >= self._auto_hide_report_threshold():
            return {
                "ok": False,
                "message": "Sesizarea nu poate fi restaurată cât timp pragul de raportări deschise este încă depășit.",
            }

        if not self._set_incident_visibility(
            incident,
            new_state=VISIBLE_INCIDENT_STATE,
            author_id=actor.id,
            message=message,
        ):
            return {"ok": False, "message": "Sesizarea este deja vizibilă."}

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a redevenit vizibilă."}

    def delete_incident_permanently(self, incident_id: int, payload, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}
        if not self._can_delete_incident(actor):
            return {"ok": False, "message": "Nu ai acces la ștergerea definitivă a sesizărilor."}

        confirmation = payload.get("confirmation", "").strip().upper()
        if confirmation != "DELETE":
            return {"ok": False, "message": "Confirmarea pentru ștergere definitivă este invalidă."}

        photo_directory = self._photo_directory(incident.id)
        self.incident_repository.delete(incident)
        db.session.commit()
        self._remove_photo_directory(photo_directory)
        return {"ok": True, "message": "Sesizarea a fost ștearsă definitiv."}

    def operator_dashboard(self, user) -> dict:
        return {
            "queue": self.incident_repository.queue_for_operator(user.department_id, include_hidden=False),
            "departments": self.department_repository.all(),
        }

    def dispatcher_dashboard(self) -> dict:
        return {
            "queue": self.incident_repository.queue_for_dispatcher(include_hidden=False),
            "departments": self.department_repository.all(),
            "open_reports": self.incident_report_repository.list_open_for_moderation(),
            "hidden_incidents": self.incident_repository.hidden_for_moderation(),
        }

    def update_incident(self, incident_id: int, payload, operator) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}

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

        return {"ok": False, "message": "Acțiunea solicitată nu este validă."}

    def update_photo_pertinence(self, incident_id: int, payload, actor) -> dict:
        incident = self.incident_repository.find(incident_id)
        if incident is None:
            return {"ok": False, "message": "Sesizarea nu a fost găsită."}
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la configurarea fotografiilor."}
        if not incident.photos:
            return {"ok": False, "message": "Sesizarea nu are fotografii."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea selecției fotografiilor este obligatorie."}

        selected_raw_ids = payload.getlist("pertinent_photo_ids") if hasattr(payload, "getlist") else []
        valid_photo_ids = {photo.id for photo in incident.photos}
        selected_photo_ids: set[int] = set()

        for raw_id in selected_raw_ids:
            if not raw_id.isdigit():
                return {"ok": False, "message": "Lista de fotografii pertinente nu este validă."}
            photo_id = int(raw_id)
            if photo_id not in valid_photo_ids:
                return {"ok": False, "message": "Una dintre fotografiile selectate nu aparține sesizării."}
            selected_photo_ids.add(photo_id)

        current_selection = {photo.id for photo in incident.photos if photo.is_pertinent}
        if current_selection == selected_photo_ids:
            return {"ok": False, "message": "Nu există modificări pentru lista fotografiilor pertinente."}

        for photo in incident.photos:
            photo.is_pertinent = photo.id in selected_photo_ids

        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=actor.id,
            message=message,
        )
        db.session.commit()
        return {"ok": True, "message": "Selecția fotografiilor pertinente a fost actualizată."}

    def notifications_for(self, viewer):
        notifications = self.notification_repository.list_for_user(viewer.id)
        return [
            {
                "notification": notification,
                "can_open_incident": notification.incident is not None and self._can_access_incident(viewer, notification.incident),
            }
            for notification in notifications
        ]

    def unread_notifications(self, user_id: int) -> int:
        return self.notification_repository.unread_count(user_id)

    def open_notification(self, notification_id: int, viewer) -> dict | None:
        notification = self.notification_repository.find_for_user(notification_id, viewer.id)
        if notification is None:
            return None

        was_marked_read = self.notification_repository.mark_as_read(notification)
        if was_marked_read:
            db.session.commit()

        return {
            "notification": notification,
            "can_open_incident": notification.incident is not None and self._can_access_incident(viewer, notification.incident),
        }

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
            "open_reports": self.incident_report_repository.list_open_for_moderation(),
            "hidden_incidents": self.incident_repository.hidden_for_moderation(),
        }

    def create_department(self, payload: dict) -> dict:
        name = payload.get("name", "").strip()
        description = payload.get("description", "").strip()
        contact_email = payload.get("contact_email", "").strip().lower()

        if not name or not description or not contact_email:
            return {"ok": False, "message": "Completează toate câmpurile departamentului."}
        if self.department_repository.find_by_name(name):
            return {"ok": False, "message": "Există deja un departament cu acest nume."}

        self.department_repository.create(name, description, contact_email)
        db.session.commit()
        return {"ok": True, "message": "Departamentul a fost creat."}

    def create_category(self, payload: dict) -> dict:
        name = payload.get("name", "").strip()
        description = payload.get("description", "").strip()
        department_id_raw = payload.get("default_department_id", "").strip()

        if not name or not description:
            return {"ok": False, "message": "Completează toate câmpurile categoriei."}
        if self.category_repository.find_by_name(name):
            return {"ok": False, "message": "Există deja o categorie cu acest nume."}

        default_department_id = None
        if department_id_raw:
            if not department_id_raw.isdigit():
                return {"ok": False, "message": "Departamentul pentru categorie nu este valid."}

            department = self.department_repository.find(int(department_id_raw))
            if department is None:
                return {"ok": False, "message": "Departamentul selectat nu există."}
            default_department_id = department.id

        self.category_repository.create(name, description, default_department_id)
        db.session.commit()
        return {"ok": True, "message": "Categoria a fost creată."}

    def _assign_department(self, incident, payload, actor) -> dict:
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la trierea sesizărilor."}

        department_id_raw = payload.get("assigned_department_id", "").strip()
        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea atribuirii este obligatorie."}
        if not department_id_raw.isdigit():
            return {"ok": False, "message": "Departamentul selectat nu este valid."}

        department = self.department_repository.find(int(department_id_raw))
        if department is None:
            return {"ok": False, "message": "Departamentul nu există."}

        if incident.status != "in_triere" and incident.assigned_department_id == department.id:
            return {"ok": False, "message": "Sesizarea este deja atribuită acestui departament."}

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

        self.notification_dispatch_service.notify_direct_in_app(
            [user.id for user in self.user_repository.staff_for_department(department.id)],
            incident,
            f'Sesizarea "{incident.title}" a fost atribuită departamentului "{department.name}".',
            exclude_user_ids={actor.id},
        )
        self.notification_dispatch_service.notify_followers(
            incident,
            f'Sesizarea "{incident.title}" a fost atribuită departamentului "{department.name}".',
            exclude_user_ids={actor.id},
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost atribuită departamentului selectat."}

    def _reject_suggested_department(self, incident, payload, actor) -> dict:
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la trierea sesizărilor."}

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
        self.notification_dispatch_service.notify_followers(
            incident,
            f'Sugestia inițială de departament pentru sesizarea "{incident.title}" a fost retrasă.',
            exclude_user_ids={actor.id},
        )

        db.session.commit()
        return {"ok": True, "message": "Sugestia de departament a fost respinsă și cazul rămâne în triere."}

    def _reject_incident(self, incident, payload, actor) -> dict:
        if not self._can_dispatch_incident(actor):
            return {"ok": False, "message": "Nu ai acces la trierea sesizărilor."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea respingerii este obligatorie."}
        if incident.status == "respinsa":
            return {"ok": False, "message": "Sesizarea este deja respinsă."}

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
        self.notification_dispatch_service.notify_followers(
            incident,
            f'Sesizarea "{incident.title}" a fost respinsă.',
            exclude_user_ids={actor.id},
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost respinsă."}

    def _mark_irrelevant_for_department(self, incident, payload, actor) -> dict:
        if not self._can_mark_irrelevant(actor, incident):
            return {"ok": False, "message": "Nu poți retrimite această sesizare la triere."}

        message = payload.get("message", "").strip()
        if not message:
            return {"ok": False, "message": "Motivarea retrimiterii la triere este obligatorie."}
        if incident.status == "in_triere":
            return {"ok": False, "message": "Sesizarea este deja în triere."}

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

        self.notification_dispatch_service.notify_direct_in_app(
            [user.id for user in self.user_repository.triage_staff()],
            incident,
            f'Sesizarea "{incident.title}" a fost retrimisă spre triere.',
            exclude_user_ids={actor.id},
        )
        self.notification_dispatch_service.notify_followers(
            incident,
            f'Sesizarea "{incident.title}" a fost retrimisă spre triere.',
            exclude_user_ids={actor.id},
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost retrimisă spre triere."}

    def _update_operational_status(self, incident, payload, actor) -> dict:
        if not self._can_update_status(actor, incident):
            return {"ok": False, "message": "Nu ai acces la gestionarea acestei sesizări."}

        status = payload.get("status", "").strip()
        message = payload.get("message", "").strip()
        if status not in OPERATOR_MANAGED_STATUSES:
            return {"ok": False, "message": "Statusul selectat nu este valid."}
        if incident.status == "in_triere":
            return {"ok": False, "message": "Sesizarea trebuie triată înainte de gestionarea operațională."}
        if status == incident.status and not message:
            return {"ok": False, "message": "Nu există nicio modificare de salvat."}

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

        self.notification_dispatch_service.notify_followers(
            incident,
            f'Sesizarea "{incident.title}" are acum statusul "{incident.status_label}".',
            exclude_user_ids={actor.id},
        )

        db.session.commit()
        return {"ok": True, "message": "Sesizarea a fost actualizată."}

    def _can_dispatch_incident(self, viewer) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and getattr(viewer, "role", None) in ["dispatcher", "admin"]
        )

    def _include_hidden_for_viewer(self, viewer) -> bool:
        return self._can_dispatch_incident(viewer)

    def _can_access_incident(self, viewer, incident) -> bool:
        if not incident.is_hidden:
            return True
        return self._include_hidden_for_viewer(viewer)

    def _can_restore_visibility(self, viewer, incident) -> bool:
        return incident.is_hidden and self._can_dispatch_incident(viewer)

    def _can_delete_incident(self, viewer) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and getattr(viewer, "role", None) == "admin"
        )

    def _auto_hide_report_threshold(self) -> int:
        return current_app.config["INCIDENT_AUTO_HIDE_REPORT_THRESHOLD"]

    def _set_incident_visibility(self, incident, *, new_state: str, author_id: int, message: str) -> bool:
        if incident.visibility_state == new_state:
            return False

        incident.visibility_state = new_state
        self.incident_repository.create_update(
            incident_id=incident.id,
            author_id=author_id,
            message=message,
            old_status=incident.status,
            new_status=incident.status,
            old_department_id=incident.assigned_department_id,
            new_department_id=incident.assigned_department_id,
        )
        return True

    def _refresh_auto_hidden_visibility(self, incident, *, actor_id: int, restored_message: str) -> None:
        if incident.visibility_state != AUTO_HIDDEN_INCIDENT_STATE:
            return
        if self.incident_report_repository.count_open_distinct_reporters(incident.id) >= self._auto_hide_report_threshold():
            return
        self._set_incident_visibility(
            incident,
            new_state=VISIBLE_INCIDENT_STATE,
            author_id=actor_id,
            message=restored_message,
        )

    def _can_operate_incident(self, viewer, incident) -> bool:
        if not getattr(viewer, "is_authenticated", False):
            return False
        if getattr(viewer, "role", None) == "admin":
            return True
        return bool(
            viewer.role == "operator"
            and viewer.department_id is not None
            and not incident.is_hidden
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

    def _can_vote(self, viewer, incident) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and incident.visibility_state == VISIBLE_INCIDENT_STATE
            and viewer.id != incident.created_by_id
        )

    def _can_report(self, viewer, incident) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and incident.visibility_state == VISIBLE_INCIDENT_STATE
            and viewer.id != incident.created_by_id
        )

    def _can_follow(self, viewer, incident) -> bool:
        return bool(
            getattr(viewer, "is_authenticated", False)
            and incident.visibility_state == VISIBLE_INCIDENT_STATE
        )

    def _can_moderate_reports(self, viewer) -> bool:
        return self._can_dispatch_incident(viewer)

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
            return "Sesizarea a fost înregistrată și așteaptă trierea inițială."
        if update.new_status == "in_triere" and update.old_status is not None:
            return "Sesizarea a fost retrimisă spre triere."
        if update.old_department_id is not None and update.new_department_id is None and update.new_status == update.old_status:
            return "Sugestia inițială de departament a fost retrasă."
        if update.new_department_id is not None and update.old_department_id != update.new_department_id:
            department_name = departments.get(update.new_department_id, "departamentul selectat")
            return f'Sesizarea a fost direcționată către departamentul "{department_name}".'
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
            return [], f'Poti incărca maximum {current_app.config["PHOTO_MAX_FILES"]} fotografii.'

        if photo_processing_status != current_app.config["PHOTO_PROCESSING_STATUS_READY"]:
            return [], "Browserul nu a finalizat procesarea fotografiilor. Încearcă din nou."

        prepared_uploads: list[PreparedPhotoUpload] = []
        max_size = current_app.config["PHOTO_MAX_FILE_SIZE_BYTES"]

        for upload in uploads:
            original_name = self._clean_photo_name(upload.filename)
            extension = Path(original_name).suffix.lower()
            if extension not in JPEG_ALLOWED_EXTENSIONS:
                return [], "Serverul acceptă doar fotografii JPEG procesate în frontend."

            mime_type = (upload.mimetype or "").lower()
            if mime_type not in JPEG_ALLOWED_MIME_TYPES:
                return [], "Tipul fotografiei încărcate nu este valid."

            content = upload.read()
            upload.stream.seek(0)

            if not content:
                return [], "Una dintre fotografii este goală."
            if len(content) > max_size:
                return [], "Una dintre fotografii depășeste limita de 5 MB după compresie."
            if not content.startswith(b"\xff\xd8") or not content.endswith(b"\xff\xd9"):
                return [], "Una dintre fotografii nu are o semnătură JPEG validă."

            dimensions = extract_jpeg_dimensions(content)
            if dimensions is None:
                return [], "Una dintre fotografii nu are o structură JPEG validă."

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

    def _remove_photo_directory(self, photo_directory: Path) -> None:
        if photo_directory.exists():
            shutil.rmtree(photo_directory, ignore_errors=True)
