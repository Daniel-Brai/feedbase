from uuid import UUID

from fastapi import status
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from lib.ext.fastapi import Service, ServiceError
from lib.pagination import CursorPaginationMetadata, CursorParams
from models import ArticleAnnotation
from repositories import ArticleAnnotationRepository, ArticleRepository
from schemas import ArticleAnnotationCreate, ArticleAnnotationOut, ArticleAnnotationUpdate


class ArticleAnnotationService(Service):
    """
    Service for managing article annotations
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.article_repo = ArticleRepository(db)
        self.article_annotation_repo = ArticleAnnotationRepository(db)

    async def list_annotations(
        self,
        user_id: int,
        article_id: UUID,
        cursor_params: CursorParams,
    ) -> tuple[str, list[ArticleAnnotationOut], CursorPaginationMetadata]:
        """
        Retrieve a paginated list of articles annotations for the specified article

        Args:
            article_id (UUID): The ID of the article to retrieve annotations for
            cursor_params (CursorParams): Pagination parameters

        Returns:
            tuple[str, list[ArticleAnnotationOut], CursorPaginationMetadata]: A tuple containing a success message
        """

        try:
            query = (
                self.article_annotation_repo.query()
                .where(
                    col(ArticleAnnotation.article_id) == article_id,
                    col(ArticleAnnotation.user_id) == user_id,
                )
                .order_by(col(ArticleAnnotation.created_at).desc())
            )

            page = await (
                self.article_annotation_repo.paginate(query=query.stmt)
                .with_params(cursor_params)
                .with_schema(ArticleAnnotation)
                .execute_cursor()
            )

            data = [ArticleAnnotationOut.from_model(annotation) for annotation in page.items]
            metadata = CursorPaginationMetadata.model_validate(page, from_attributes=True)

            return "Annotations retrieved successfully", data, metadata
        except Exception as e:
            self.logger.error("Failed to retrieve annotations", error=str(e), exc_info=e)
            raise ServiceError("Failed to retrieve annotations") from e

    async def get_article_annotation_count(
        self,
        user_id: int,
        article_id: UUID,
    ) -> tuple[str, int, None]:
        """
        Get the total number of annotations the authenticated user has for a specific article.

        Args:
            user_id (int): The ID of the authenticated user.
            article_id (UUID): The ID of the article.

        Returns:
            tuple[str, int, None]: A tuple containing a success message, the annotation count, and None for metadata.
        """

        try:
            count = (
                await self.article_annotation_repo.query()
                .where(
                    col(ArticleAnnotation.article_id) == article_id,
                    col(ArticleAnnotation.user_id) == user_id,
                )
                .count()
            )

            return "Annotation count retrieved successfully", count, None
        except Exception as e:
            self.logger.error(
                "Failed to retrieve article annotation count",
                article_id=str(article_id),
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to retrieve article annotation count") from e

    async def add_article_annotation(
        self, user_id: int, data: ArticleAnnotationCreate
    ) -> tuple[str, ArticleAnnotationOut, None]:
        """
        Add an annotation to an article.

        Args:
            user_id (int): The ID of the user adding the annotation
            data (ArticleAnnotationCreate): The data for the new annotation

        Returns:
            tuple[str, ArticleAnnotationOut, None]: A tuple containing a success message and the created annotation

        Raises:
            ServiceError: If the annotation creation fails, if the article is not found
        """

        try:
            existing_article = await self.article_repo.get(data.article_id)
            if not existing_article:
                raise ServiceError("Article not found", status_code=status.HTTP_404_NOT_FOUND)

            new_annotation_data = {
                **data.model_dump(),
                "user_id": user_id,
            }

            article_annotation = await self.article_annotation_repo.create(new_annotation_data)
            await self.article_annotation_repo.commit()

            return (
                "Annotation added successfully",
                ArticleAnnotationOut.from_model(article_annotation),
                None,
            )

        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to add annotation",
                article_id=str(data.article_id),
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to add annotation") from e

    async def update_article_annotation(
        self, user_id: int, annotation_id: UUID, data: ArticleAnnotationUpdate
    ) -> tuple[str, ArticleAnnotationOut, None]:
        """
        Update an article annotation.

        Args:
            user_id (int): The ID of the user performing the update
            annotation_id (UUID): The ID of the annotation to update
            data (ArticleAnnotationUpdate): The new data for the annotation

        Returns:
            tuple[str, ArticleAnnotationOut, None]: A tuple containing a success message and the updated annotation

        Raises:
            ServiceError: If the annotation is not found or if the update fails
        """

        try:
            existing_article_annotation = await self.article_annotation_repo.get_by(id=annotation_id, user_id=user_id)
            if not existing_article_annotation:
                raise ServiceError("Annotation not found", status_code=status.HTTP_404_NOT_FOUND)

            update_data = data.model_dump(exclude_unset=True, exclude_none=True)

            article_annotation = await self.article_annotation_repo.update_with_obj(
                existing_article_annotation, update_data
            )

            await self.article_annotation_repo.commit()

            await self.article_annotation_repo.refresh(article_annotation)

            return (
                "Annotation updated successfully",
                ArticleAnnotationOut.from_model(article_annotation),
                None,
            )
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to update annotation",
                annotation_id=str(annotation_id),
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to update annotation") from e

    async def delete_article_annotation(self, user_id: int, annotation_id: UUID) -> str:
        """
        Delete an article annotation.

        Args:
            user_id (int): The ID of the user performing the deletion
            annotation_id (UUID): The ID of the annotation to delete

        Returns:
            str: A success message

        Raises:
            ServiceError: If the annotation is not found or if the deletion fails
        """

        try:
            existing_article_annotation = await self.article_annotation_repo.get(annotation_id)
            if not existing_article_annotation:
                raise ServiceError("Annotation not found", status_code=status.HTTP_404_NOT_FOUND)

            await self.article_annotation_repo.delete_with_obj(existing_article_annotation)
            await self.article_annotation_repo.commit()

            return "Annotation deleted successfully"
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to delete annotation",
                annotation_id=str(annotation_id),
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to delete annotation") from e
