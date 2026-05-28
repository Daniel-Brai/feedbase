from fastapi import FastAPI

from lib.exceptions import CorsConfiguration, configure_exception_handler, create_exception_handler, create_problem
from settings import settings


def configure_exceptions(app: FastAPI):
    """
    Configure exception handling for the app

    See :func:`~lib.exceptions.configure_exception_handler` for more details
    """

    from lib.ext.fastapi import ServiceError
    from lib.openapi.exceptions import OpenAPIAuthError
    from lib.throttler.exceptions import ThrottlerError

    cors = CorsConfiguration(
        allow_origins=[str(url) for url in settings.APP_CORS_ORIGINS],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    return configure_exception_handler(
        app,
        create_exception_handler(
            cors,
            {
                ServiceError: create_problem(title="Service Error"),
                OpenAPIAuthError: create_problem(title="OpenAPI Authentication Error"),
                ThrottlerError: create_problem(title="Throttler Error"),
            },
        ),
    )
