from enums import NotificationEventEmitterBackend
from lib.notifications import PushSubscriptionKeys, PushSubscriptionService, PushSubscriptionType, VAPIDClaims
from lib.notifications import configure_notifications as _configure_notifications
from lib.notifications.emitter import redis_emitter_from_url
from settings import settings


def configure_notifications():
    """
    Configure the notifications system for the application.

    See :meth:`~lib.notifications.configure_notifications` for more details on the configuration options.
    """

    from bootstrap.database import engine, get_db
    from models import User

    async def load_push_subscriptions(user):
        async with get_db() as session:
            svc = PushSubscriptionService(session)
            rows = await svc.get_for_user(user.id)
            return [
                PushSubscriptionType(
                    endpoint=row.endpoint,
                    keys=PushSubscriptionKeys(p256dh=row.p256dh, auth=row.auth),
                )
                for row in rows
            ]

    async def prune_push_subscriptions(user, expired_endpoints: list[str]):
        async with get_db() as session:
            svc = PushSubscriptionService(session)
            await svc.prune_expired(user_id=user.id, endpoints=expired_endpoints)

    event_emitter = (
        redis_emitter_from_url(
            str(settings.APP_REDIS_URL),
            max_connections=5,
            socket_timeout=10.0,
            socket_connect_timeout=10.0,
            health_check_interval=30,
            decode_responses=False,
        )
        if settings.USE_NOTIFICATION_EVENT_EMITTER_BACKEND == NotificationEventEmitterBackend.REDIS
        else None
    )

    return _configure_notifications(
        engine=engine,
        event_emitter=event_emitter,
        vapid_claims=VAPIDClaims(sub=settings.VAPID_CLAIMS_SUBJECT),
        vapid_private_key=open(settings.VAPID_PRIVATE_KEY_PATH, encoding="utf-8").read(),
        push_subscription_pruner=prune_push_subscriptions,
        push_subscription_loader=load_push_subscriptions,
        recipient_models={
            "User": User,
        },
        route_prefix=f"{settings.API_V1_STR}/notifications",
    )
