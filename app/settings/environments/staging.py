from enums import Environment

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """
    Staging configuration settings.

    Inherits from :class:`BaseSettings` and overrides any attributes as necessary for the staging environment.
    """

    APP_ENVIRONMENT: Environment = Environment.STAGING
