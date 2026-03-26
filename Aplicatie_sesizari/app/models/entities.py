from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

ROLE_CHOICES = [
    ("citizen", "Cetățean"),
    ("operator", "Operator"),
    ("dispatcher", "Dispecer"),
    ("admin", "Administrator"),
]
ROLE_LABELS = dict(ROLE_CHOICES)

INCIDENT_PRIORITY_CHOICES = [
    ("scazuta", "Scazută"),
    ("medie", "Medie"),
    ("ridicata", "Ridicată"),
    ("critica", "Critică"),
]
PRIORITY_LABELS = dict(INCIDENT_PRIORITY_CHOICES)

STATUS_COUNT_LABELS = {
    "in_triere": ("În triere", "În triere"),
    "noua": ("Nouă", "Noi"),
    "in_verificare": ("În verificare", "În verificare"),
    "redirectionata": ("Redirecționată", "Redirecționate"),
    "in_lucru": ("În lucru", "În lucru"),
    "rezolvata": ("Rezolvată", "Rezolvate"),
    "respinsa": ("Respinsă", "Respinse"),
}


INCIDENT_STATUS_CHOICES = [
    ("in_triere", "În triere"),
    ("noua", "Nouă"),
    ("in_verificare", "În verificare"),
    ("redirectionata", "Redirecționată"),
    ("in_lucru", "În lucru"),
    ("rezolvata", "Rezolvată"),
    ("respinsa", "Respinsă"),
]
STATUS_LABELS = dict(INCIDENT_STATUS_CHOICES)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    contact_email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    categories = db.relationship("Category", back_populates="default_department")
    users = db.relationship("User", back_populates="department")
    incidents = db.relationship(
        "Incident",
        back_populates="assigned_department",
        foreign_keys="Incident.assigned_department_id",
    )
    suggested_incidents = db.relationship(
        "Incident",
        back_populates="suggested_department",
        foreign_keys="Incident.suggested_department_id",
    )


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="citizen")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    department = db.relationship("Department", back_populates="users")
    incidents = db.relationship("Incident", back_populates="creator", foreign_keys="Incident.created_by_id")
    updates = db.relationship("IncidentUpdate", back_populates="author")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)


class Category(db.Model):
    __tablename__ = "incident_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    default_department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    default_department = db.relationship("Department", back_populates="categories")
    incidents = db.relationship("Incident", back_populates="category")


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    priority = db.Column(db.String(32), nullable=False, default="medie")
    status = db.Column(db.String(32), nullable=False, default="noua")
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("incident_categories.id"), nullable=False)
    suggested_department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    assigned_department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, nullable=False, onupdate=utc_now)

    creator = db.relationship("User", back_populates="incidents", foreign_keys=[created_by_id])
    category = db.relationship("Category", back_populates="incidents")
    suggested_department = db.relationship(
        "Department",
        back_populates="suggested_incidents",
        foreign_keys=[suggested_department_id],
    )
    assigned_department = db.relationship(
        "Department",
        back_populates="incidents",
        foreign_keys=[assigned_department_id],
    )
    photos = db.relationship(
        "IncidentPhoto",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentPhoto.created_at.asc()",
    )
    updates = db.relationship(
        "IncidentUpdate",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentUpdate.created_at.desc()",
    )
    notifications = db.relationship("Notification", back_populates="incident")

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS.get(self.priority, self.priority)

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def display_department_label(self) -> str:
        if self.status == "in_triere":
            if self.suggested_department is not None:
                return f"Sugerat: {self.suggested_department.name}"
            return "In asteptarea trierii"

        if self.assigned_department is not None:
            return self.assigned_department.name

        return "-"


class IncidentPhoto(db.Model):
    __tablename__ = "incident_photos"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    original_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(64), nullable=False, default="image/jpeg")
    size_bytes = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    is_pertinent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    incident = db.relationship("Incident", back_populates="photos")


class IncidentUpdate(db.Model):
    __tablename__ = "incident_updates"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    old_status = db.Column(db.String(32))
    new_status = db.Column(db.String(32))
    old_department_id = db.Column(db.Integer)
    new_department_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    incident = db.relationship("Incident", back_populates="updates")
    author = db.relationship("User", back_populates="updates")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User", back_populates="notifications")
    incident = db.relationship("Incident", back_populates="notifications")
