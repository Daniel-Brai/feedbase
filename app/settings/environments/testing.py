from enums import Environment

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """
    Test environment settings.

    Inherits from :class:`BaseSettings` and overrides any attributes as necessary for testing.
    """

    APP_ENVIRONMENT: Environment = Environment.TEST
