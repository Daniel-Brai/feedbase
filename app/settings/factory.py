from functools import lru_cache

from pydantic import ValidationError

from enums import Environment
from lib.logger import get_logger
from settings.environments import BaseSettings, DevelopmentSettings, ProductionSettings, StagingSettings, TestSettings

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_settings() -> BaseSettings:
    """
    Returns the appropriate settings based on the environment.

    Returns:
        BaseSettings: The settings for the specified environment

    Raises:
        ValueError: If an invalid environment is specified
    """

    settings = BaseSettings()  # type: ignore

    environment = settings.APP_ENVIRONMENT

    settings_map: dict[Environment, type[BaseSettings]] = {
        Environment.DEVELOPMENT: DevelopmentSettings,
        Environment.PRODUCTION: ProductionSettings,
        Environment.TEST: TestSettings,
        Environment.STAGING: StagingSettings,
    }

    if environment not in settings_map:
        raise ValueError(
            f"Invalid environment: {environment.value}. " f"Must be one of {"".join(settings_map.keys())}."
        )

    return settings_map[environment]()  # type: ignore


try:
    settings = _get_settings()
except ValidationError as e:
    logger.error(f"Settings validation error: {e}")
    raise
