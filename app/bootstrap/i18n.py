from fastapi import FastAPI

from lib.i18n import I18n, I18nMiddleware
from settings import settings

i18n = I18n(
    default_locale=settings.APP_DEFAULT_LOCALE,
    fallback_locale=settings.APP_FALLBACK_LOCALE,
    locales_dir=settings.APP_LOCALES_DIR,
)


def configure_i18n(
    app: FastAPI,
) -> None:
    """
    Configure internationalization (i18n) for the application.

    Args:
        app (FastAPI): The FastAPI application instance to configure.

    Returns:
        None
    """

    app.add_middleware(
        I18nMiddleware, i18n=i18n, locale_cookie_name=settings.APP_LOCALE_COOKIE_NAME, expose_locale_header=True
    )
