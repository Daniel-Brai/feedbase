from typing import Annotated

from fastapi import Depends

from services import FolderService

from .database import AsyncDBSessionDep


def get_folder_service(db: AsyncDBSessionDep) -> FolderService:
    """
    Dependency provider for `FolderService`.
    """

    return FolderService(db)


FolderServiceDep = Annotated[FolderService, Depends(get_folder_service)]
