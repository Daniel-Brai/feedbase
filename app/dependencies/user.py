from typing import Annotated

from fastapi import Depends

from services import UserService

from .database import AsyncDBSessionDep


def get_user_service(db: AsyncDBSessionDep) -> UserService:
    """
    Dependency provider for `UserService`.
    """

    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
