from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.repositories import (
    CategoryRepository,
    DepartmentRepository,
    IncidentPhotoRepository,
    IncidentRepository,
    NotificationRepository,
    UserRepository,
)
from app.services import IncidentService

api_bp = Blueprint("api", __name__, url_prefix="/api")


def build_incident_service() -> IncidentService:
    return IncidentService(
        IncidentRepository(),
        CategoryRepository(),
        DepartmentRepository(),
        UserRepository(),
        NotificationRepository(),
        IncidentPhotoRepository(),
    )


@api_bp.get("/incidents/markers")
@login_required
def incident_markers():
    service = build_incident_service()
    return jsonify({"markers": service.marker_payload(request.args.to_dict())})


@api_bp.get("/notifications/unread-count")
@login_required
def unread_notifications():
    service = build_incident_service()
    return jsonify({"unread_count": service.unread_notifications(current_user.id)})
