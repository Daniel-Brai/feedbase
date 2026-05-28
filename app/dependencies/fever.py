from typing import Annotated

from fastapi import Depends

from services import FeverService

from .database import AsyncDBSessionDep


def get_fever_service(db: AsyncDBSessionDep) -> FeverService:
    """
    Dependency provider for `FeverService`.
    """

    return FeverService(db)


FeverServiceDep = Annotated[FeverService, Depends(get_fever_service)]
