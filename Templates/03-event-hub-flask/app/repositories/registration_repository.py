from app.extensions import db
from app.models.entities import Registration


class RegistrationRepository:
    def count_for_event(self, event_id: int) -> int:
        return Registration.query.filter_by(event_id=event_id).count()

    def find_for_event_and_attendee(self, event_id: int, attendee_id: int) -> Registration | None:
        return Registration.query.filter_by(event_id=event_id, attendee_id=attendee_id).first()

    def create(self, event_id: int, attendee_id: int) -> Registration:
        registration = Registration(event_id=event_id, attendee_id=attendee_id, status="registered")
        db.session.add(registration)
        db.session.commit()
        return registration

