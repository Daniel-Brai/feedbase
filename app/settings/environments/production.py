from enums import Environment

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """
    Production configuration settings.

    Inherits from :class:`~settings.environments.base.Settings` and overrides any attributes as needed for production deployment.
    """

    APP_ENVIRONMENT: Environment = Environment.PRODUCTION
