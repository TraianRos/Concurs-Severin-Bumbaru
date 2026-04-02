from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.entities import Notification


class NotificationRepository:
    def list_for_user(self, user_id: int) -> list[Notification]:
        return (
            Notification.query.options(joinedload(Notification.incident))
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def find_for_user(self, notification_id: int, user_id: int) -> Notification | None:
        return (
            Notification.query.options(joinedload(Notification.incident))
            .filter_by(id=notification_id, user_id=user_id)
            .first()
        )

    def unread_count(self, user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    def create(self, user_id: int, incident_id: int, message: str) -> Notification:
        notification = Notification(user_id=user_id, incident_id=incident_id, message=message)
        db.session.add(notification)
        db.session.flush()
        return notification

    def create_many(self, user_ids: list[int], incident_id: int, message: str) -> None:
        unique_ids = sorted(set(user_ids))
        for user_id in unique_ids:
            db.session.add(Notification(user_id=user_id, incident_id=incident_id, message=message))

    def mark_all_as_read(self, user_id: int) -> int:
        notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for notification in notifications:
            notification.is_read = True
        return len(notifications)

    def mark_as_read(self, notification: Notification) -> bool:
        if notification.is_read:
            return False
        notification.is_read = True
        return True
