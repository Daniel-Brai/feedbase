from fastapi import FastAPI

from enums import Environment
from lib.openapi import configure_openapi as _configure_openapi
from settings import settings


def configure_openapi(app: FastAPI):
    """
    Configure OpenAPI documentation for the FastAPI application, including authentication and environment-specific settings.

    If environent is staging or production, basic auth for the docs using the provided username and password in settings is enabled.

    See :func:`~lib.openapi.configure_openapi` for details.
    """

    return _configure_openapi(
        app,
        username=settings.OPENAPI_USERNAME,
        password=settings.OPENAPI_PASSWORD,
        docs_url=settings.OPENAPI_DOCS_URL,
        json_schema_url=settings.OPENAPI_JSON_SCHEMA_URL,
        use_default_security=(
            True if settings.APP_ENVIRONMENT in [Environment.STAGING, Environment.PRODUCTION] else False
        ),
    )
