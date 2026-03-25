from app.extensions import db
from app.models.entities import Attendee


class AttendeeRepository:
    def find_by_email(self, email: str) -> Attendee | None:
        return Attendee.query.filter_by(email=email).first()

    def create(self, full_name: str, email: str) -> Attendee:
        attendee = Attendee(full_name=full_name, email=email)
        db.session.add(attendee)
        db.session.commit()
        return attendee

