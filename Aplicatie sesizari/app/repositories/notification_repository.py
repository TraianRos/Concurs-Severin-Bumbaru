from app.extensions import db
from app.models.entities import Notification


class NotificationRepository:
    def list_for_user(self, user_id: int) -> list[Notification]:
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    def unread_count(self, user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    def create_many(self, user_ids: list[int], incident_id: int, message: str) -> None:
        unique_ids = sorted(set(user_ids))
        for user_id in unique_ids:
            db.session.add(Notification(user_id=user_id, incident_id=incident_id, message=message))

    def mark_all_as_read(self, user_id: int) -> int:
        notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for notification in notifications:
            notification.is_read = True
        return len(notifications)
