from typing import Annotated

from fastapi import Depends

from services import HealthService


def get_health_service() -> HealthService:
    """
    Dependency provider for `HealthService`.
    """

    return HealthService()


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
