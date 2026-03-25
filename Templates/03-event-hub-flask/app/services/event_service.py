from app.repositories.attendee_repository import AttendeeRepository
from app.repositories.event_repository import EventRepository
from app.repositories.registration_repository import RegistrationRepository


class EventService:
    def __init__(
        self,
        event_repository: EventRepository,
        attendee_repository: AttendeeRepository,
        registration_repository: RegistrationRepository,
    ) -> None:
        self.event_repository = event_repository
        self.attendee_repository = attendee_repository
        self.registration_repository = registration_repository

    def homepage_data(self) -> dict:
        return {"events": self.event_repository.upcoming()}

    def list_events(self) -> list:
        return self.event_repository.all()

    def create_event(self, payload: dict) -> dict:
        title = payload.get("title", "").strip()
        location = payload.get("location", "").strip()
        start_date = payload.get("start_date", "").strip()
        seats = int(payload.get("seats", 0) or 0)

        if not title or not location or not start_date or seats < 1:
            return {"ok": False, "message": "All event fields are required."}

        self.event_repository.create(title, location, start_date, seats)
        return {"ok": True, "message": "Event created successfully."}

    def get_event(self, event_id: int):
        return self.event_repository.find(event_id)

    def register_attendee(self, event_id: int, payload: dict) -> dict:
        full_name = payload.get("full_name", "").strip()
        email = payload.get("email", "").strip().lower()

        if not full_name or not email:
            return {"ok": False, "message": "Name and email are required."}

        event = self.event_repository.find(event_id)
        if event is None:
            return {"ok": False, "message": "Event not found."}

        if self.registration_repository.count_for_event(event_id) >= event.seats:
            return {"ok": False, "message": "No seats left for this event."}

        attendee = self.attendee_repository.find_by_email(email)
        if attendee is None:
            attendee = self.attendee_repository.create(full_name, email)

        if self.registration_repository.find_for_event_and_attendee(event_id, attendee.id):
            return {"ok": False, "message": "This attendee is already registered."}

        self.registration_repository.create(event_id, attendee.id)
        return {"ok": True, "message": "Registration completed."}

