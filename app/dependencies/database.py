from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from bootstrap.database import get_db_pool
from lib.database import AsyncSession


async def get_db_dependency() -> AsyncGenerator[AsyncSession, None]:
    async with get_db_pool() as session:
        yield session


AsyncDBSessionDep = Annotated[AsyncSession, Depends(get_db_dependency)]
