from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from lib.database import Repository
from models.article_status import ArticleStatus


class ArticleStatusRepository(Repository[ArticleStatus, UUID]):
    """
    Repository for managing status related to articles, such as read/unread status, starred status, and other user-specific metadata.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ArticleStatus, db)
