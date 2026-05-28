from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from lib.database import Repository
from models import ArticleAnnotation


class ArticleAnnotationRepository(Repository[ArticleAnnotation, UUID]):
    """
    Repository for managing article annotations
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ArticleAnnotation, db)
