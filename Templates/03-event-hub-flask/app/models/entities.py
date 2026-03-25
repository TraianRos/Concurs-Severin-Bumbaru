from datetime import datetime

from app.extensions import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.String(64), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    registrations = db.relationship("Registration", back_populates="event", cascade="all, delete-orphan")


class Attendee(db.Model):
    __tablename__ = "attendees"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    registrations = db.relationship("Registration", back_populates="attendee", cascade="all, delete-orphan")


class Registration(db.Model):
    __tablename__ = "registrations"
    __table_args__ = (db.UniqueConstraint("event_id", "attendee_id", name="uq_event_attendee"),)

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    attendee_id = db.Column(db.Integer, db.ForeignKey("attendees.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(32), default="registered", nullable=False)

    event = db.relationship("Event", back_populates="registrations")
    attendee = db.relationship("Attendee", back_populates="registrations")

