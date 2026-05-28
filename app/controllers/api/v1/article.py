from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path

from dependencies import ArticleAnnotationServiceDep, ArticleServiceDep, AuthDep
from filters import ArticleFilter
from lib.ext.fastapi import Controller, IResponse, ORJSONResponse, before_action, get, patch
from lib.pagination import CursorPaginationMetadata, CursorParams, FilterDepends
from schemas import ArticleAnnotationOut, ArticleOut, ArticleStatsOut, ArticleStatusOut, ArticleStatusUpdate
from settings import settings


class ArticleController(Controller):
    """
    API controller for managing articles parsed from feeds.
    """

    prefix = f"{settings.API_V1_STR}/articles"

    @before_action
    def authenticate(self, user: AuthDep):
        self.current_user = user

    @get(
        "",
        operation_id="list_articles",
        response_model=IResponse[list[ArticleOut], CursorPaginationMetadata],
    )
    async def list_articles(
        self,
        cursor: Annotated[CursorParams, Depends()],
        filter: Annotated[ArticleFilter, FilterDepends(ArticleFilter)],
        service: ArticleServiceDep,
    ) -> ORJSONResponse:
        """
        List articles for the authenticated user
        """

        message, data, metadata = await service.list_articles(self.current_user.id, cursor, filter)
        return self.json(message=message, data=data, metadata=metadata)

    @get(
        "/{article_id}",
        operation_id="get_article",
        response_model=IResponse[ArticleOut, None],
    )
    async def get_article(
        self,
        article_id: Annotated[UUID, Path(..., description="The ID of the article to retrieve")],
        service: ArticleServiceDep,
    ) -> ORJSONResponse:
        """
        Get a specific article by ID for the authenticated user
        """

        message, data, metadata = await service.get_article(self.current_user.id, article_id)
        return self.json(message=message, data=data)

    @get(
        "/stats",
        operation_id="get_article_stats",
        response_model=IResponse[ArticleStatsOut, None],
    )
    async def get_article_stats(
        self,
        service: ArticleServiceDep,
    ) -> ORJSONResponse:
        """
        Get counts of articles by status (e.g., all articles, unread, starred, bookmarked, today) for the authenticated user
        """

        message, data, metadata = await service.get_article_stats(self.current_user.id)
        return self.json(message=message, data=data)

    @get(
        "/{article_id}/annotations",
        operation_id="get_article_annotations",
        response_model=IResponse[list[ArticleAnnotationOut], CursorPaginationMetadata],
    )
    async def get_article_annotations(
        self,
        article_id: Annotated[
            UUID,
            Path(..., description="The ID of the article to retrieve annotations for"),
        ],
        cursor: Annotated[CursorParams, Depends()],
        service: ArticleAnnotationServiceDep,
    ) -> ORJSONResponse:
        """
        Get annotations for a specific article by ID for the authenticated user
        """

        message, data, metadata = await service.list_annotations(self.current_user.id, article_id, cursor)
        return self.json(message=message, data=data, metadata=metadata)

    @get(
        "/{article_id}/annotations/count",
        operation_id="get_article_annotation_count",
        response_model=IResponse[int, None],
        include_in_schema=False,
    )
    async def get_article_annotation_count(
        self,
        article_id: Annotated[
            UUID,
            Path(
                ...,
                description="The ID of the article to retrieve annotation count for",
            ),
        ],
        service: ArticleAnnotationServiceDep,
    ) -> ORJSONResponse:
        """
        Get the total number of annotations the authenticated user has for a specific article.
        """

        message, data, metadata = await service.get_article_annotation_count(self.current_user.id, article_id)
        return self.json(message=message, data=data, metadata=metadata)

    @patch(
        "/{article_id}/status",
        operation_id="update_article_status",
        response_model=IResponse[ArticleStatusOut, None],
    )
    async def update_article_status(
        self,
        article_id: Annotated[UUID, Path(..., description="The ID of the article to update")],
        body: Annotated[
            ArticleStatusUpdate,
            Body(..., description="The new status for the article (e.g., read/unread)"),
        ],
        service: ArticleServiceDep,
    ) -> ORJSONResponse:
        """
        Update the status of a specific article for the authenticated user
        """

        message, data, _ = await service.update_article_status(self.current_user.id, article_id, body)
        return self.json(message=message, data=data)
