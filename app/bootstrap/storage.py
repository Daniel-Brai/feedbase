from pathlib import Path

from enums import Environment
from lib.storage import configure_storage as _configure_storage
from settings import settings


def configure_storage():
    """
    Configure the file storage system.

    If production, use S3, staging use Cloudinary and for others use local storage.

    See :func:`~lib.storage.configure_storage` for details.
    """

    environment = settings.APP_ENVIRONMENT

    if environment == Environment.PRODUCTION:
        return _configure_storage(
            provider="S3",
            key_or_path=settings.FILE_STORAGE_S3_ACCESS_KEY_ID,  # type: ignore
            secret=settings.FILE_STORAGE_S3_SECRET_ACCESS_KEY,  # type: ignore
            container=settings.FILE_STORAGE_S3_BUCKET_NAME,  # type: ignore
            region=settings.FILE_STORAGE_S3_REGION,  # type: ignore
        )

    elif environment == Environment.STAGING:
        return _configure_storage(
            provider="CLOUDINARY",
            key_or_path=settings.FILE_STORAGE_CLOUDINARY_API_KEY,  # type: ignore
            secret=settings.FILE_STORAGE_CLOUDINARY_API_SECRET,  # type: ignore
            container=settings.FILE_STORAGE_CLOUDINARY_FOLDER,  # type: ignore
            cloud_name=settings.FILE_STORAGE_CLOUDINARY_CLOUD_NAME,  # type: ignore
        )

    return _configure_storage(
        key_or_path=str(Path(settings.APP_DIR) / "uploads"),
    )
