from datetime import UTC, datetime

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
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

INCIDENT_REPORT_REASON_CHOICES = [
    ("duplicat", "Duplicat"),
    ("abuz_sau_spam", "Abuz sau spam"),
    ("informatie_incorecta", "Informație incorectă"),
    ("alt_motiv", "Alt motiv"),
]
INCIDENT_REPORT_REASON_LABELS = dict(INCIDENT_REPORT_REASON_CHOICES)

INCIDENT_REPORT_STATUS_CHOICES = [
    ("deschis", "Deschis"),
    ("confirmat", "Confirmat"),
    ("respins", "Respins"),
]
INCIDENT_REPORT_STATUS_LABELS = dict(INCIDENT_REPORT_STATUS_CHOICES)

INCIDENT_VISIBILITY_STATE_CHOICES = [
    ("visible", "Vizibilă"),
    ("auto_hidden", "Ascunsă automat"),
    ("confirmed_hidden", "Ascunsă după confirmare"),
]
INCIDENT_VISIBILITY_STATE_LABELS = dict(INCIDENT_VISIBILITY_STATE_CHOICES)

FOLLOW_CHANNEL_CHOICES = [
    ("in_app", "În aplicație"),
    ("email", "Email"),
    ("web_push", "Notificări pe dispozitiv"),
]
FOLLOW_CHANNEL_LABELS = dict(FOLLOW_CHANNEL_CHOICES)

DELIVERY_CHANNEL_CHOICES = [
    ("email", "Email"),
    ("web_push", "Web push"),
]
DELIVERY_CHANNEL_LABELS = dict(DELIVERY_CHANNEL_CHOICES)

DELIVERY_STATUS_CHOICES = [
    ("sent", "Livrat"),
    ("failed", "Eșuat"),
]
DELIVERY_STATUS_LABELS = dict(DELIVERY_STATUS_CHOICES)


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
    votes = db.relationship("IncidentVote", back_populates="user", cascade="all, delete-orphan")
    reports_made = db.relationship(
        "IncidentReport",
        back_populates="reporter",
        cascade="all, delete-orphan",
        foreign_keys="IncidentReport.reporter_id",
    )
    reviewed_reports = db.relationship(
        "IncidentReport",
        back_populates="reviewer",
        foreign_keys="IncidentReport.reviewer_id",
    )
    follows = db.relationship("IncidentFollow", back_populates="user", cascade="all, delete-orphan")
    web_push_subscriptions = db.relationship(
        "WebPushSubscription",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="WebPushSubscription.created_at.desc()",
    )
    delivery_logs = db.relationship("NotificationDeliveryLog", back_populates="user")

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
    visibility_state = db.Column(db.String(32), nullable=False, default="visible")
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
    notifications = db.relationship("Notification", back_populates="incident", cascade="all, delete-orphan")
    votes = db.relationship("IncidentVote", back_populates="incident", cascade="all, delete-orphan")
    reports = db.relationship(
        "IncidentReport",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentReport.created_at.desc()",
    )
    follows = db.relationship("IncidentFollow", back_populates="incident", cascade="all, delete-orphan")
    delivery_logs = db.relationship("NotificationDeliveryLog", back_populates="incident", cascade="all, delete-orphan")

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS.get(self.priority, self.priority)

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def visibility_state_label(self) -> str:
        return INCIDENT_VISIBILITY_STATE_LABELS.get(self.visibility_state, self.visibility_state)

    @property
    def is_hidden(self) -> bool:
        return self.visibility_state != "visible"

    @property
    def display_department_label(self) -> str:
        if self.status == "in_triere":
            if self.suggested_department is not None:
                return f"Sugerat: {self.suggested_department.name}"
            return "In asteptarea trierii"

        if self.assigned_department is not None:
            return self.assigned_department.name

        return "-"

    @property
    def vote_count(self) -> int:
        return len(self.votes)

    @property
    def open_report_count(self) -> int:
        return len([report for report in self.reports if report.status == "deschis"])

    @property
    def open_reporter_count(self) -> int:
        return len({report.reporter_id for report in self.reports if report.status == "deschis"})


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


class IncidentVote(db.Model):
    __tablename__ = "incident_votes"
    __table_args__ = (UniqueConstraint("incident_id", "user_id", name="uq_incident_vote"),)

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    incident = db.relationship("Incident", back_populates="votes")
    user = db.relationship("User", back_populates="votes")


class WebPushSubscription(db.Model):
    __tablename__ = "web_push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    endpoint = db.Column(db.String(1000), nullable=False, unique=True)
    p256dh_key = db.Column(db.String(255), nullable=False)
    auth_key = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    last_seen_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User", back_populates="web_push_subscriptions")
    follows = db.relationship("IncidentFollow", back_populates="push_subscription")


class IncidentFollow(db.Model):
    __tablename__ = "incident_follows"
    __table_args__ = (UniqueConstraint("incident_id", "user_id", name="uq_incident_follow"),)

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    in_app_enabled = db.Column(db.Boolean, default=False, nullable=False)
    email_enabled = db.Column(db.Boolean, default=False, nullable=False)
    push_subscription_id = db.Column(db.Integer, db.ForeignKey("web_push_subscriptions.id"))
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, nullable=False, onupdate=utc_now)

    incident = db.relationship("Incident", back_populates="follows")
    user = db.relationship("User", back_populates="follows")
    push_subscription = db.relationship("WebPushSubscription", back_populates="follows")

    @property
    def web_push_enabled(self) -> bool:
        return (
            self.push_subscription_id is not None
            and self.push_subscription is not None
            and self.push_subscription.is_active
            and self.push_subscription.user_id == self.user_id
        )

    @property
    def has_any_channel(self) -> bool:
        return self.in_app_enabled or self.email_enabled or self.web_push_enabled

    @property
    def active_channels(self) -> tuple[str, ...]:
        channels = []
        if self.in_app_enabled:
            channels.append("in_app")
        if self.email_enabled:
            channels.append("email")
        if self.web_push_enabled:
            channels.append("web_push")
        return tuple(channels)


class IncidentReport(db.Model):
    __tablename__ = "incident_reports"
    __table_args__ = (UniqueConstraint("incident_id", "reporter_id", name="uq_incident_reporter"),)

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reason = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="deschis")
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    resolution_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    reviewed_at = db.Column(db.DateTime)

    incident = db.relationship("Incident", back_populates="reports")
    reporter = db.relationship("User", back_populates="reports_made", foreign_keys=[reporter_id])
    reviewer = db.relationship("User", back_populates="reviewed_reports", foreign_keys=[reviewer_id])

    @property
    def reason_label(self) -> str:
        return INCIDENT_REPORT_REASON_LABELS.get(self.reason, self.reason)

    @property
    def status_label(self) -> str:
        return INCIDENT_REPORT_STATUS_LABELS.get(self.status, self.status)


class NotificationDeliveryLog(db.Model):
    __tablename__ = "notification_delivery_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    channel = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User", back_populates="delivery_logs")
    incident = db.relationship("Incident", back_populates="delivery_logs")

    @property
    def channel_label(self) -> str:
        return DELIVERY_CHANNEL_LABELS.get(self.channel, self.channel)

    @property
    def status_label(self) -> str:
        return DELIVERY_STATUS_LABELS.get(self.status, self.status)
