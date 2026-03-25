from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.repositories.attendee_repository import AttendeeRepository
from app.repositories.event_repository import EventRepository
from app.repositories.registration_repository import RegistrationRepository
from app.services.event_service import EventService

web_bp = Blueprint("web", __name__)


def build_service() -> EventService:
    return EventService(EventRepository(), AttendeeRepository(), RegistrationRepository())


@web_bp.get("/")
def home():
    service = build_service()
    return render_template("home.html", events=service.homepage_data()["events"], page_title="Upcoming events")


@web_bp.get("/events")
def events():
    service = build_service()
    return render_template("events.html", events=service.list_events(), page_title="All events")


@web_bp.route("/events/new", methods=["GET", "POST"])
def new_event():
    service = build_service()

    if request.method == "POST":
        result = service.create_event(request.form)
        flash(result["message"])
        return redirect(url_for("web.events" if result["ok"] else "web.new_event"))

    return render_template("new-event.html", page_title="Create event")


@web_bp.get("/events/<int:event_id>")
def event_detail(event_id: int):
    service = build_service()
    event = service.get_event(event_id)
    if event is None:
        return ("Not found", 404)

    return render_template("event-detail.html", event=event, page_title=event.title)


@web_bp.post("/events/<int:event_id>/register")
def register(event_id: int):
    service = build_service()
    result = service.register_attendee(event_id, request.form)
    flash(result["message"])
    return redirect(url_for("web.event_detail", event_id=event_id))


@web_bp.get("/health")
def health():
    return jsonify({"status": "ok", "app": "event-hub"})

