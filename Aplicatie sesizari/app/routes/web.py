from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import INCIDENT_PRIORITY_CHOICES, INCIDENT_STATUS_CHOICES
from app.repositories import (
    CategoryRepository,
    DepartmentRepository,
    IncidentRepository,
    NotificationRepository,
    UserRepository,
)
from app.services import AuthService, IncidentService

web_bp = Blueprint("web", __name__)


def build_auth_service() -> AuthService:
    return AuthService(UserRepository(), DepartmentRepository())


def build_incident_service() -> IncidentService:
    return IncidentService(
        IncidentRepository(),
        CategoryRepository(),
        DepartmentRepository(),
        UserRepository(),
        NotificationRepository(),
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


@web_bp.get("/")
def home():
    service = build_incident_service()
    return render_template("home.html", page_title="Platforma de raportare", **service.homepage_data())


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.home"))

    if request.method == "POST":
        result = build_auth_service().register_citizen(request.form)
        flash(result["message"])
        if result["ok"]:
            return redirect(url_for("web.login"))

    return render_template("register.html", page_title="Creeaza cont")


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.home"))

    if request.method == "POST":
        result = build_auth_service().authenticate(request.form.get("email", ""), request.form.get("password", ""))
        flash(result["message"])
        if result["ok"]:
            login_user(result["user"])
            next_url = request.args.get("next")
            return redirect(next_url or url_for("web.home"))

    return render_template("login.html", page_title="Autentificare")


@web_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Ai fost deconectat.")
    return redirect(url_for("web.home"))


@web_bp.get("/incidents")
@login_required
def incidents():
    service = build_incident_service()
    filters = request.args.to_dict()
    return render_template(
        "incidents.html",
        page_title="Lista sesizari",
        incidents=service.list_incidents(filters),
        filters=filters,
        include_leaflet=True,
        **service.filter_options(),
    )


@web_bp.route("/incidents/new", methods=["GET", "POST"])
@role_required("citizen", "operator", "admin")
def new_incident():
    service = build_incident_service()

    if request.method == "POST":
        result = service.create_incident(request.form, current_user)
        flash(result["message"])
        if result["ok"]:
            return redirect(url_for("web.incident_detail", incident_id=result["incident"].id))

    return render_template(
        "incident_form.html",
        page_title="Sesizare noua",
        include_leaflet=True,
        categories=service.filter_options()["categories"],
        priority_choices=INCIDENT_PRIORITY_CHOICES,
    )


@web_bp.get("/incidents/<int:incident_id>")
@login_required
def incident_detail(incident_id: int):
    service = build_incident_service()
    incident = service.get_incident(incident_id)
    if incident is None:
        return ("Not found", 404)

    return render_template(
        "incident_detail.html",
        page_title=incident.title,
        incident=incident,
        include_leaflet=True,
        departments=service.filter_options()["departments"],
        status_choices=INCIDENT_STATUS_CHOICES,
    )


@web_bp.post("/incidents/<int:incident_id>/update")
@role_required("operator", "admin")
def incident_update(incident_id: int):
    service = build_incident_service()
    result = service.update_incident(incident_id, request.form, current_user)
    flash(result["message"])
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
    )


@web_bp.post("/admin/departments")
@role_required("admin")
def admin_create_department():
    result = build_incident_service().create_department(request.form)
    flash(result["message"])
    return redirect(url_for("web.admin_dashboard"))


@web_bp.post("/admin/categories")
@role_required("admin")
def admin_create_category():
    result = build_incident_service().create_category(request.form)
    flash(result["message"])
    return redirect(url_for("web.admin_dashboard"))


@web_bp.post("/admin/operators")
@role_required("admin")
def admin_create_operator():
    result = build_auth_service().create_operator(request.form)
    flash(result["message"])
    return redirect(url_for("web.admin_dashboard"))


@web_bp.get("/notifications")
@login_required
def notifications():
    service = build_incident_service()
    return render_template(
        "notifications.html",
        page_title="Notificari",
        notifications=service.notifications_for(current_user.id),
    )


@web_bp.post("/notifications/read-all")
@login_required
def mark_notifications_read():
    service = build_incident_service()
    count = service.mark_all_notifications_as_read(current_user.id)
    flash(f"Au fost marcate ca citite {count} notificari.")
    return redirect(url_for("web.notifications"))


@web_bp.get("/health")
def health():
    return {"status": "ok", "app": "aplicatie-sesizari"}
