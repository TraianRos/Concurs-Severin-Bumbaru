from app.extensions import db
from app.models.entities import Event


class EventRepository:
    def all(self) -> list[Event]:
        return Event.query.order_by(Event.start_date.asc()).all()

    def upcoming(self, limit: int = 3) -> list[Event]:
        return Event.query.order_by(Event.start_date.asc()).limit(limit).all()

    def find(self, event_id: int) -> Event | None:
        return db.session.get(Event, event_id)

    def create(self, title: str, location: str, start_date: str, seats: int) -> Event:
        event = Event(title=title, location=location, start_date=start_date, seats=seats)
        db.session.add(event)
        db.session.commit()
        return event

