from urllib.parse import urlparse

from lib.auth import AuthMailer, AuthOptions, Hasher, SessionBackend
from lib.auth import configure_auth as _configure_auth
from lib.notifications import PushSubscriptionService
from settings import settings


def configure_auth():
    """
    Configure the authentication system for the application, including session management, OAuth providers, and email services.

    See the :func:`~lib.auth.configure_auth` for more details on the authentication system and its components.
    """

    from bootstrap.authorization import authorization
    from bootstrap.database import engine
    from models import User

    site_url = urlparse(settings.APP_SITE_URL)
    cookie_domain = site_url.hostname if site_url.hostname not in ("localhost", "127.0.0.1", "::1") else None

    async def delete_push_subscriptions(session, user):
        await PushSubscriptionService(session).unregister_all(user_id=user.id)

    return _configure_auth(
        backend=SessionBackend(
            secret_key=settings.AUTH_SESSION_SECRET_KEY,
            cookie_name=settings.AUTH_SESSION_COOKIE_NAME,
            auto_login_on_register=True,
            secure=settings.APP_DOMAIN_SECURE,
            domain=cookie_domain,
        ),
        engine=engine,
        user_model=User,
        auth_route_prefix=f"{settings.API_V1_STR}/auth",
        mailer=AuthMailer(base_url=settings.APP_SITE_URL),
        hasher=Hasher.configure(),
        authorization=authorization,
        options=AuthOptions(
            registration_enabled=False, deletion_style="hard", deletion_callbacks=[delete_push_subscriptions]
        ),
    )
