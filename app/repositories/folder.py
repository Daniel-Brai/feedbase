from uuid import UUID

from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from lib.database import Repository
from models.folder import Folder


class FolderRepository(Repository[Folder, UUID]):
    """
    Repository for managing folders
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Folder, db)

    async def get_user_folders(self, user_id: int) -> list[Folder]:
        results = await self.query().where(col(Folder.user_id) == user_id).all()
        return list(results)
