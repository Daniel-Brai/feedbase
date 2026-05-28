from datetime import datetime

from enums import Environment, MailerBackend
from lib.mailer import ConsoleTransport, Mailer, SESTransport, SMTPTransport
from lib.mailer import configure_mailer as _configure_mailer
from settings import settings


def configure_mailer():
    """
    Configure the mailer system.

    If the environment is "production" or "staging", it will use SMTP with the settings defined in the environment variables.

    Otherwise, it will use a console transport that prints emails to the console, which is useful for development and testing.

    See :func:`~lib.mailer.configure_mailer` for details.
    """

    environment = settings.APP_ENVIRONMENT
    backend = settings.USE_MAILER_BACKEND

    if backend == MailerBackend.SMTP:
        transport = SMTPTransport(
            host=settings.MAILER_SMTP_HOST,
            port=settings.MAILER_SMTP_PORT,
            username=settings.MAILER_SMTP_USER,
            password=settings.MAILER_SMTP_PASSWORD,
            use_tls=settings.MAILER_SMTP_TLS,
            use_ssl=settings.MAILER_SMTP_SSL,
        )
    elif backend == MailerBackend.SES:
        transport = SESTransport(
            region=settings.MAILER_SES_REGION_NAME,
            aws_access_key_id=settings.MAILER_SES_ACCESS_KEY_ID,  # type: ignore[attr-defined]
            aws_secret_access_key=settings.MAILER_SES_SECRET_ACCESS_KEY,  # type: ignore[attr-defined]
        )
    else:
        transport = ConsoleTransport()

    mailer = _configure_mailer(
        Mailer(
            transport=transport,
            from_email=settings.MAILER_DEFAULT_SENDER_EMAIL,
            from_name=settings.MAILER_DEFAULT_SENDER_NAME,  # type: ignore[attr-defined]
            templates_dir=settings.APP_MAILER_TEMPLATES_DIR,
            assets_dir=settings.APP_ASSETS_DIR,
            auto_reload=(True if environment in [Environment.DEVELOPMENT, Environment.TEST] else False),
            verify_on_startup=settings.MAILER_VERIFY_ON_STARTUP,
            globals={
                "APP_NAME": settings.APP_NAME,
                "APP_URL": settings.APP_SITE_URL,
                "now": datetime.now,
            },
        )
    )

    return mailer
