from app.extensions import db
from app.models.entities import NotificationDeliveryLog


class NotificationDeliveryLogRepository:
    def create(
        self,
        *,
        user_id: int,
        incident_id: int,
        channel: str,
        status: str,
        error_message: str | None = None,
    ) -> NotificationDeliveryLog:
        log_entry = NotificationDeliveryLog(
            user_id=user_id,
            incident_id=incident_id,
            channel=channel,
            status=status,
            error_message=error_message,
        )
        db.session.add(log_entry)
        db.session.flush()
        return log_entry
