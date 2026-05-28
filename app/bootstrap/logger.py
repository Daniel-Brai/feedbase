from lib.logger import configure_logging as _configure_logging
from settings import settings


def configure_logging():
    """
    Configure logging for the application.
    """

    _configure_logging(
        log_level=settings.APP_LOG_LEVEL,
    )
