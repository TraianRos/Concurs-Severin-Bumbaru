from app.extensions import db
from app.models.entities import WebPushSubscription, utc_now


class WebPushSubscriptionRepository:
    def find(self, subscription_id: int) -> WebPushSubscription | None:
        return WebPushSubscription.query.filter_by(id=subscription_id).first()

    def find_by_endpoint(self, endpoint: str) -> WebPushSubscription | None:
        return WebPushSubscription.query.filter_by(endpoint=endpoint).first()

    def create_or_update(
        self,
        *,
        user_id: int,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
    ) -> WebPushSubscription:
        subscription = self.find_by_endpoint(endpoint)
        if subscription is None:
            subscription = WebPushSubscription(
                user_id=user_id,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key,
                is_active=True,
            )
            db.session.add(subscription)
        else:
            if subscription.user_id != user_id:
                # A push endpoint belongs to one browser/device. If another user
                # claims the same endpoint, old follows must lose that device link.
                for follow in list(subscription.follows):
                    follow.push_subscription_id = None
            subscription.user_id = user_id
            subscription.p256dh_key = p256dh_key
            subscription.auth_key = auth_key
            subscription.is_active = True

        subscription.last_seen_at = utc_now()

        db.session.flush()
        return subscription

    def deactivate(self, subscription: WebPushSubscription) -> None:
        subscription.is_active = False
