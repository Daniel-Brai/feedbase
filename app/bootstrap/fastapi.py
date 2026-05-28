from fastapi import FastAPI

from settings import settings


def create_fastapi_app() -> FastAPI:
    """
    Create and return the FastAPI app instance.

    This is called by the ASGI server (e.g. Uvicorn) to get the app instance to run.
    The app is configured with metadata and the lifespan function for startup/shutdown events.
    The OpenAPI docs are disabled by default but can be enabled if needed.
    """

    from bootstrap.lifespan import lifespan

    fastapi_app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )

    return fastapi_app
