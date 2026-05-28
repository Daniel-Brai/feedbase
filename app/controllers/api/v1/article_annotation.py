from typing import Annotated
from uuid import UUID

from fastapi import Body, Path

from dependencies import ArticleAnnotationServiceDep, AuthDep
from lib.ext.fastapi import Controller, IBaseResponse, IResponse, ORJSONResponse, before_action, delete, patch, post
from schemas import ArticleAnnotationCreate, ArticleAnnotationOut, ArticleAnnotationUpdate
from settings import settings


class ArticleAnnotationController(Controller):
    """
    API controller for managing article annotations
    """

    prefix = f"{settings.API_V1_STR}/annotations"

    tags = ["Annotations"]

    @before_action
    def authenticate(self, user: AuthDep):
        self.current_user = user

    @post(
        "",
        operation_id="add_annotation",
        response_model=IResponse[ArticleAnnotationOut, None],
    )
    async def add_annotation(
        self,
        body: Annotated[
            ArticleAnnotationCreate,
            Body(..., description="The content of the annotation to add to the article"),
        ],
        service: ArticleAnnotationServiceDep,
    ) -> ORJSONResponse:
        """
        Add an annotation to a specific article by ID for the authenticated user
        """

        message, data, metadata = await service.add_article_annotation(self.current_user.id, body)
        return self.json(message=message, data=data, metadata=metadata)

    @patch(
        "/{annotation_id}",
        operation_id="update_annotation",
        response_model=IResponse[ArticleAnnotationOut, None],
    )
    async def update_annotation(
        self,
        annotation_id: Annotated[UUID, Path(description="The ID of the annotation to update")],
        body: Annotated[ArticleAnnotationUpdate, Body(description="The updated annotation data")],
        service: ArticleAnnotationServiceDep,
    ) -> ORJSONResponse:
        """
        Update an existing article annotation
        """

        message, data, metadata = await service.update_article_annotation(self.current_user.id, annotation_id, body)
        return self.json(message=message, data=data, metadata=metadata)

    @delete(
        "/{annotation_id}",
        operation_id="delete_annotation",
        response_model=IBaseResponse,
    )
    async def delete_annotation(
        self,
        annotation_id: Annotated[UUID, Path(description="The ID of the annotation to delete")],
        service: ArticleAnnotationServiceDep,
    ) -> ORJSONResponse:
        """
        Delete an existing article annotation
        """

        message = await service.delete_article_annotation(self.current_user.id, annotation_id)
        return self.json(message=message)
