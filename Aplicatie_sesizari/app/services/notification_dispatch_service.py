import json
import smtplib
from email.message import EmailMessage

from flask import current_app, url_for

from app.repositories.incident_follow_repository import IncidentFollowRepository
from app.repositories.notification_delivery_log_repository import NotificationDeliveryLogRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.web_push_subscription_repository import WebPushSubscriptionRepository


class NotificationDispatchService:
    def __init__(
        self,
        notification_repository: NotificationRepository,
        incident_follow_repository: IncidentFollowRepository,
        delivery_log_repository: NotificationDeliveryLogRepository,
        web_push_subscription_repository: WebPushSubscriptionRepository,
    ) -> None:
        self.notification_repository = notification_repository
        self.incident_follow_repository = incident_follow_repository
        self.delivery_log_repository = delivery_log_repository
        self.web_push_subscription_repository = web_push_subscription_repository

    def notify_direct_in_app(
        self,
        user_ids: list[int],
        incident,
        message: str,
        *,
        exclude_user_ids: set[int] | None = None,
    ) -> None:
        excluded = exclude_user_ids or set()
        recipients = [user_id for user_id in user_ids if user_id not in excluded]
        if recipients:
            self.notification_repository.create_many(recipients, incident.id, message)

    def notify_followers(
        self,
        incident,
        message: str,
        *,
        exclude_user_ids: set[int] | None = None,
    ) -> None:
        excluded = exclude_user_ids or set()

        for follow in self.incident_follow_repository.list_for_incident(incident.id):
            if follow.user_id in excluded or not follow.has_any_channel:
                continue

            if follow.in_app_enabled:
                self.notification_repository.create_many([follow.user_id], incident.id, message)

            if follow.email_enabled:
                self._send_follow_email(follow.user, incident, message)

            if follow.web_push_enabled:
                self._send_follow_web_push(follow, incident, message)

    def _send_follow_email(self, user, incident, message: str) -> None:
        smtp_host = current_app.config.get("SMTP_HOST", "").strip()
        from_email = current_app.config.get("SMTP_FROM_EMAIL", "").strip()

        if not smtp_host or not from_email:
            self.delivery_log_repository.create(
                user_id=user.id,
                incident_id=incident.id,
                channel="email",
                status="failed",
                error_message="Configurarea SMTP nu este completă.",
            )
            return

        subject_prefix = current_app.config.get("EMAIL_SUBJECT_PREFIX", current_app.config.get("APP_NAME", ""))
        subject = f"{subject_prefix}: actualizare pentru sesizarea \"{incident.title}\""
        body = (
            f"{message}\n\n"
            f"Vezi sesizarea aici: {self._incident_url(incident.id)}\n\n"
            f"Acest mesaj a fost generat automat de platformă."
        )

        try:
            self._send_email(user.email, subject, body)
        except Exception as exc:  # pragma: no cover - exercised by monkeypatch in tests
            self.delivery_log_repository.create(
                user_id=user.id,
                incident_id=incident.id,
                channel="email",
                status="failed",
                error_message=str(exc),
            )
            return

        self.delivery_log_repository.create(
            user_id=user.id,
            incident_id=incident.id,
            channel="email",
            status="sent",
        )

    def _send_follow_web_push(self, follow, incident, message: str) -> None:
        subscription = follow.push_subscription
        if not follow.web_push_enabled or subscription is None:
            return

        public_key = current_app.config.get("WEB_PUSH_PUBLIC_KEY", "").strip()
        private_key = current_app.config.get("WEB_PUSH_PRIVATE_KEY", "").strip()
        subject = current_app.config.get("WEB_PUSH_SUBJECT", "").strip()

        if not public_key or not private_key or not subject:
            self.delivery_log_repository.create(
                user_id=follow.user_id,
                incident_id=incident.id,
                channel="web_push",
                status="failed",
                error_message="Configurarea Web Push nu este completă.",
            )
            return

        payload = {
            "title": current_app.config.get("APP_NAME", "Aplicație de sesizări"),
            "body": message,
            "url": self._incident_url(incident.id),
            "incidentId": incident.id,
        }

        try:
            self._send_web_push(
                {
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh_key,
                        "auth": subscription.auth_key,
                    },
                },
                payload,
            )
        except Exception as exc:  # pragma: no cover - exercised by monkeypatch in tests
            error_message = str(exc)
            if "410" in error_message or "404" in error_message:
                self.web_push_subscription_repository.deactivate(subscription)
                follow.push_subscription_id = None

            self.delivery_log_repository.create(
                user_id=follow.user_id,
                incident_id=incident.id,
                channel="web_push",
                status="failed",
                error_message=error_message,
            )
            return

        self.delivery_log_repository.create(
            user_id=follow.user_id,
            incident_id=incident.id,
            channel="web_push",
            status="sent",
        )

    def _send_email(self, to_email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = current_app.config["SMTP_FROM_EMAIL"]
        message["To"] = to_email
        message.set_content(body)

        smtp_host = current_app.config["SMTP_HOST"]
        smtp_port = int(current_app.config.get("SMTP_PORT", 587))
        smtp_username = current_app.config.get("SMTP_USERNAME", "").strip()
        smtp_password = current_app.config.get("SMTP_PASSWORD", "")
        smtp_use_tls = bool(current_app.config.get("SMTP_USE_TLS", True))
        smtp_use_ssl = bool(current_app.config.get("SMTP_USE_SSL", False))
        timeout = float(current_app.config.get("SMTP_TIMEOUT_SECONDS", 10))

        smtp_class = smtplib.SMTP_SSL if smtp_use_ssl else smtplib.SMTP
        with smtp_class(smtp_host, smtp_port, timeout=timeout) as smtp:
            if not smtp_use_ssl and smtp_use_tls:
                smtp.starttls()
            if smtp_username:
                smtp.login(smtp_username, smtp_password)
            smtp.send_message(message)

    def _send_web_push(self, subscription_info: dict, payload: dict) -> None:
        try:
            from pywebpush import webpush
        except ImportError as exc:  # pragma: no cover - depends on optional dependency
            raise RuntimeError("Biblioteca pywebpush nu este instalată.") from exc

        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=current_app.config["WEB_PUSH_PRIVATE_KEY"],
            vapid_claims={"sub": current_app.config["WEB_PUSH_SUBJECT"]},
        )

    def _incident_url(self, incident_id: int) -> str:
        return url_for("web.incident_detail", incident_id=incident_id, _external=True)
