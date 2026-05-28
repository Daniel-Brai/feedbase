from pathlib import Path

from enums import Environment
from lib.assets import configure_asset_manager as _configure_asset_manager
from settings import settings


def configure_asset_manager():
    """
    Configures the asset manager
    """

    from bootstrap.templates import template_engine

    return _configure_asset_manager(
        engine=template_engine,
        manifest_path=(Path("assets/dist/assets.json") if settings.APP_ENVIRONMENT == Environment.PRODUCTION else None),
        static_url=settings.APP_STATIC_URL,
        mode="rename",
        static_dir=(
            Path("assets/src") if not settings.APP_ENVIRONMENT == Environment.PRODUCTION else Path("assets/dist")
        ),
    )
