from typing import Annotated

from fastapi import Depends

from services import ArticleAnnotationService, ArticleService

from .database import AsyncDBSessionDep


def get_article_service(db: AsyncDBSessionDep) -> ArticleService:
    """
    Dependency provider for `ArticleService`.
    """

    return ArticleService(db)


def get_article_annotation_service(db: AsyncDBSessionDep) -> ArticleAnnotationService:
    """
    Dependency provider for `ArticleAnnotationService`.
    """

    return ArticleAnnotationService(db)


ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]
ArticleAnnotationServiceDep = Annotated[ArticleAnnotationService, Depends(get_article_annotation_service)]
