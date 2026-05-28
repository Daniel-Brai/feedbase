from fastapi import FastAPI

from settings import settings


def configure_static(app: FastAPI) -> None:
    """
    Configure static file serving for the FastAPI application.
    """

    from fastapi.staticfiles import StaticFiles

    app.mount(
        settings.APP_STATIC_URL,
        StaticFiles(directory=settings.APP_ASSETS_DIR),
        name="static",
    )
