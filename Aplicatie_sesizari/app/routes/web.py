from functools import wraps

from flask import Blueprint, abort, current_app, flash, make_response, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import INCIDENT_PRIORITY_CHOICES
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
from app.services import AuthService, IncidentService, NotificationDispatchService

web_bp = Blueprint("web", __name__)


def build_auth_service() -> AuthService:
    return AuthService(UserRepository(), DepartmentRepository())


def build_notification_dispatch_service(
    notification_repository: NotificationRepository,
    incident_follow_repository: IncidentFollowRepository,
    web_push_subscription_repository: WebPushSubscriptionRepository,
) -> NotificationDispatchService:
    return NotificationDispatchService(
        notification_repository,
        incident_follow_repository,
        NotificationDeliveryLogRepository(),
        web_push_subscription_repository,
    )


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
        build_notification_dispatch_service(
            notification_repository,
            incident_follow_repository,
            web_push_subscription_repository,
        ),
    )


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def flash_result(result: dict) -> None:
    flash(result["message"], "success" if result.get("ok") else "error")


@web_bp.get("/")
def home():
    service = build_incident_service()
    return render_template("home.html", page_title="Platformă de raportare", **service.homepage_data(current_user))


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.home"))

    if request.method == "POST":
        result = build_auth_service().register_citizen(request.form)
        flash_result(result)
        if result["ok"]:
            return redirect(url_for("web.login"))

    return render_template("register.html", page_title="Creează cont")


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.home"))

    if request.method == "POST":
        result = build_auth_service().authenticate(request.form.get("email", ""), request.form.get("password", ""))
        flash_result(result)
        if result["ok"]:
            login_user(result["user"])
            next_url = request.args.get("next")
            return redirect(next_url or url_for("web.home"))

    return render_template("login.html", page_title="Autentificare")


@web_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Ai fost deconectat.", "info")
    return redirect(url_for("web.home"))


@web_bp.get("/incidents")
@login_required
def incidents():
    service = build_incident_service()
    filters = request.args.to_dict()
    search_limit = int(current_app.config.get("FORM_LIMITS", {}).get("incident_search", 120))
    search = filters.get("search", "").strip()
    if len(search) > search_limit:
        filters["search"] = search[:search_limit]
        flash(f"Căutarea a fost limitată la maximum {search_limit} de caractere.", "error")
    return render_template(
        "incidents.html",
        page_title="Listă sesizări",
        incidents=service.list_incidents(filters, current_user),
        filters=filters,
        include_leaflet=True,
        **service.filter_options(),
    )


@web_bp.route("/incidents/new", methods=["GET", "POST"])
@role_required("citizen", "operator", "dispatcher", "admin")
def new_incident():
    service = build_incident_service()
    filter_options = service.filter_options()

    if request.method == "POST":
        result = service.create_incident(request.form, request.files, current_user)
        flash_result(result)
        if result["ok"]:
            return redirect(url_for("web.incident_detail", incident_id=result["incident"].id))

    return render_template(
        "incident_form.html",
        page_title="Sesizare nouă",
        include_leaflet=True,
        categories=filter_options["categories"],
        departments=filter_options["departments"],
        photo_options=service.photo_form_options(),
        priority_choices=INCIDENT_PRIORITY_CHOICES,
    )


@web_bp.get("/incidents/<int:incident_id>")
@login_required
def incident_detail(incident_id: int):
    service = build_incident_service()
    context = service.incident_detail_context(incident_id, current_user)
    if context is None:
        return ("Not found", 404)

    return render_template(
        "incident_detail.html",
        page_title=context["incident"].title,
        include_leaflet=True,
        **context,
    )


@web_bp.get("/incidents/<int:incident_id>/photos/<int:photo_id>")
@login_required
def incident_photo(incident_id: int, photo_id: int):
    service = build_incident_service()
    photo = service.get_incident_photo(incident_id, photo_id, current_user)
    if photo is None:
        abort(404)

    photo_path = service.photo_storage_path(incident_id, photo.stored_name)
    if not photo_path.is_file():
        abort(404)

    return send_file(
        photo_path,
        mimetype=photo.mime_type,
        download_name=photo.original_name,
        conditional=True,
    )


@web_bp.post("/incidents/<int:incident_id>/update")
@role_required("operator", "dispatcher", "admin")
def incident_update(incident_id: int):
    service = build_incident_service()
    result = service.update_incident(incident_id, request.form, current_user)
    flash_result(result)
    return redirect(url_for("web.incident_detail", incident_id=incident_id))


@web_bp.post("/incidents/<int:incident_id>/vote")
@login_required
def incident_vote(incident_id: int):
    service = build_incident_service()
    result = service.toggle_vote(incident_id, current_user)
    flash_result(result)
    if service.incident_detail_context(incident_id, current_user) is None:
        return redirect(url_for("web.incidents"))
    return redirect(url_for("web.incident_detail", incident_id=incident_id))


@web_bp.post("/incidents/<int:incident_id>/follow")
@login_required
def incident_follow(incident_id: int):
    service = build_incident_service()
    result = service.update_follow_preferences(incident_id, request.form, current_user)
    flash_result(result)
    if service.incident_detail_context(incident_id, current_user) is None:
        return redirect(url_for("web.incidents"))
    return redirect(url_for("web.incident_detail", incident_id=incident_id))


@web_bp.post("/incidents/<int:incident_id>/report")
@login_required
def incident_report(incident_id: int):
    service = build_incident_service()
    result = service.submit_report(incident_id, request.form, current_user)
    flash_result(result)
    if service.incident_detail_context(incident_id, current_user) is None:
        return redirect(url_for("web.incidents"))
    return redirect(url_for("web.incident_detail", incident_id=incident_id))


@web_bp.post("/incident-reports/<int:report_id>/review")
@role_required("dispatcher", "admin")
def incident_report_review(report_id: int):
    service = build_incident_service()
    result = service.review_report(report_id, request.form, current_user)
    flash_result(result)
    incident_id = result.get("incident_id")
    if incident_id:
        return redirect(url_for("web.incident_detail", incident_id=incident_id))
    return redirect(request.referrer or url_for("web.dispatcher_dashboard"))


@web_bp.post("/incidents/<int:incident_id>/visibility/restore")
@role_required("dispatcher", "admin")
def incident_restore_visibility(incident_id: int):
    service = build_incident_service()
    result = service.restore_visibility(incident_id, request.form, current_user)
    flash_result(result)
    return redirect(url_for("web.incident_detail", incident_id=incident_id))


@web_bp.post("/incidents/<int:incident_id>/photos/pertinence")
@role_required("dispatcher", "admin")
def incident_photo_pertinence(incident_id: int):
    service = build_incident_service()
    result = service.update_photo_pertinence(incident_id, request.form, current_user)
    flash_result(result)
    return redirect(url_for("web.incident_detail", incident_id=incident_id))


@web_bp.get("/dashboard/operator")
@role_required("operator", "admin")
def operator_dashboard():
    service = build_incident_service()
    data = service.operator_dashboard(current_user)
    return render_template(
        "operator_dashboard.html",
        page_title="Dashboard operator",
        queue=data["queue"],
        departments=data["departments"],
    )


@web_bp.get("/dashboard/dispatcher")
@role_required("dispatcher", "admin")
def dispatcher_dashboard():
    service = build_incident_service()
    data = service.dispatcher_dashboard()
    return render_template(
        "dispatcher_dashboard.html",
        page_title="Dashboard triere",
        queue=data["queue"],
        departments=data["departments"],
        open_reports=data["open_reports"],
        hidden_incidents=data["hidden_incidents"],
    )


@web_bp.get("/dashboard/admin")
@role_required("admin")
def admin_dashboard():
    service = build_incident_service()
    data = service.admin_dashboard_data()
    return render_template(
        "admin_dashboard.html",
        page_title="Administrare",
        departments=data["departments"],
        categories=data["categories"],
        operators=data["operators"],
        users=data["users"],
        open_reports=data["open_reports"],
        hidden_incidents=data["hidden_incidents"],
    )


@web_bp.post("/admin/departments")
@role_required("admin")
def admin_create_department():
    result = build_incident_service().create_department(request.form)
    flash_result(result)
    return redirect(url_for("web.admin_dashboard"))


@web_bp.post("/admin/categories")
@role_required("admin")
def admin_create_category():
    result = build_incident_service().create_category(request.form)
    flash_result(result)
    return redirect(url_for("web.admin_dashboard"))


@web_bp.post("/admin/operators")
@role_required("admin")
def admin_create_operator():
    result = build_auth_service().create_staff(request.form)
    flash_result(result)
    return redirect(url_for("web.admin_dashboard"))


@web_bp.post("/admin/incidents/<int:incident_id>/delete")
@role_required("admin")
def admin_delete_incident(incident_id: int):
    result = build_incident_service().delete_incident_permanently(incident_id, request.form, current_user)
    flash_result(result)
    if result.get("ok"):
        return redirect(url_for("web.admin_dashboard"))
    return redirect(request.referrer or url_for("web.admin_dashboard"))


@web_bp.get("/notifications")
@login_required
def notifications():
    service = build_incident_service()
    return render_template(
        "notifications.html",
        page_title="Notificări",
        notifications=service.notifications_for(current_user),
    )


@web_bp.get("/notifications/<int:notification_id>/open")
@login_required
def open_notification(notification_id: int):
    service = build_incident_service()
    result = service.open_notification(notification_id, current_user)
    if result is None:
        abort(404)

    notification = result["notification"]
    if result["can_open_incident"]:
        return redirect(url_for("web.incident_detail", incident_id=notification.incident_id))

    flash("Sesizarea nu mai este disponibilă pentru rolul tău curent.", "info")
    return redirect(url_for("web.notifications"))


@web_bp.post("/notifications/read-all")
@login_required
def mark_notifications_read():
    service = build_incident_service()
    count = service.mark_all_notifications_as_read(current_user.id)
    flash(f"Au fost marcate ca citite {count} notificări.", "success")
    return redirect(url_for("web.notifications"))


@web_bp.get("/push-sw.js")
def push_service_worker():
    response = make_response(
        """
self.addEventListener("push", (event) => {
    if (!event.data) {
        return;
    }

    const payload = event.data.json();
    event.waitUntil(
        self.registration.showNotification(payload.title || "Notificare", {
            body: payload.body || "",
            data: { url: payload.url || "/" },
            tag: payload.incidentId ? `incident-${payload.incidentId}` : "incident-update",
        })
    );
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    const targetUrl = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : "/";

    event.waitUntil(clients.openWindow(targetUrl));
});
        """.strip()
    )
    response.mimetype = "application/javascript"
    response.headers["Cache-Control"] = "no-cache"
    return response


@web_bp.get("/health")
def health():
    return {"status": "ok", "app": "aplicatie-sesizari"}
