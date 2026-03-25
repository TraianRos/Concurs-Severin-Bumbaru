from app import create_app
from app.extensions import db
from app.models.entities import Attendee, Event, Registration

app = create_app()

with app.app_context():
    db.create_all()

    if Event.query.count() == 0:
        db.session.add_all(
            [
                Event(title="Backend Basics", location="Lab 101", start_date="2026-04-02 10:00", seats=30),
                Event(title="Frontend Sprint", location="Lab 204", start_date="2026-04-03 12:00", seats=24),
            ]
        )
        db.session.commit()

    if Attendee.query.count() == 0:
        attendee = Attendee(full_name="Ana Ionescu", email="ana@example.com")
        db.session.add(attendee)
        db.session.commit()

        registration = Registration(event_id=1, attendee_id=attendee.id, status="registered")
        db.session.add(registration)
        db.session.commit()

    print("Database ready.")

