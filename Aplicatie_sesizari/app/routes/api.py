from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.repositories import (
    CategoryRepository,
    DepartmentRepository,
    IncidentFollowRepository,
    IncidentPhotoRepository,
    IncidentReportRepository,
    IncidentRepository,
    IncidentVoteRepository,
    NotificationDeliveryLogRepository,
    NotificationRepository,
    UserRepository,
    WebPushSubscriptionRepository,
)
from app.services import IncidentService, NotificationDispatchService

api_bp = Blueprint("api", __name__, url_prefix="/api")


def build_incident_service() -> IncidentService:
    notification_repository = NotificationRepository()
    incident_follow_repository = IncidentFollowRepository()
    web_push_subscription_repository = WebPushSubscriptionRepository()
    return IncidentService(
        IncidentRepository(),
        CategoryRepository(),
        DepartmentRepository(),
        UserRepository(),
        notification_repository,
        IncidentPhotoRepository(),
        IncidentVoteRepository(),
        IncidentReportRepository(),
        incident_follow_repository,
        web_push_subscription_repository,
        NotificationDispatchService(
            notification_repository,
            incident_follow_repository,
            NotificationDeliveryLogRepository(),
            web_push_subscription_repository,
        ),
    )


@api_bp.get("/incidents/markers")
@login_required
def incident_markers():
    service = build_incident_service()
    return jsonify({"markers": service.marker_payload(request.args.to_dict(), current_user)})


@api_bp.get("/notifications/unread-count")
@login_required
def unread_notifications():
    service = build_incident_service()
    return jsonify({"unread_count": service.unread_notifications(current_user.id)})


@api_bp.post("/push/subscriptions")
@login_required
def push_subscriptions():
    service = build_incident_service()
    result = service.register_push_subscription(current_user, request.get_json(silent=True) or {})
    status_code = 200 if result.get("ok") else 400
    payload = {"ok": result.get("ok", False), "message": result.get("message", "")}
    if result.get("ok"):
        payload["subscription_id"] = result["subscription"].id
    return jsonify(payload), status_code
