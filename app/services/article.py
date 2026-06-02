from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import contains_eager, selectinload, with_loader_criteria
from sqlmodel import and_, col, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from filters import ArticleFilter
from lib.ext.fastapi import Service, ServiceError
from lib.pagination import CursorPaginationMetadata, CursorParams
from models import Article, ArticleStatus, Feed, FeedSubscription
from repositories import ArticleRepository, ArticleStatusRepository
from schemas import ArticleOut, ArticleStatsOut, ArticleStatusOut, ArticleStatusUpdate


class ArticleService(Service):
    """
    Service for managing articles and their states.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.article_repo = ArticleRepository(db)
        self.article_status_repo = ArticleStatusRepository(db)

    async def list_articles(
        self,
        user_id: int,
        cursor_params: CursorParams,
        filter_params: ArticleFilter | None = None,
    ) -> tuple[str, list[ArticleOut], CursorPaginationMetadata]:
        """
        Retrieve a paginated list of articles for the specified user

        Args:
            user_id (int): The ID of the user to retrieve articles for
            cursor_params (CursorParams): Pagination parameters
            filter_params (Filter | None): Optional filter parameters to apply to the query

        Returns:
            tuple[str, list[ArticleOut], CursorPaginationMetadata]: A tuple containing a success message
        """

        try:
            query = self.article_repo.query()

            if filter_params and filter_params.statuses and filter_params.statuses.is_read is False:
                query = query.outerjoin(
                    ArticleStatus,
                    and_(
                        ArticleStatus.article_id == Article.id,
                        ArticleStatus.user_id == user_id,
                    ),
                ).where(
                    or_(
                        col(ArticleStatus.is_read) == False,
                        col(ArticleStatus.id).is_(None),
                    )
                )

                filter_params = filter_params.model_copy(update={"statuses": None})
            else:
                query = query.outerjoin(
                    ArticleStatus,
                    and_(
                        ArticleStatus.article_id == Article.id,
                        ArticleStatus.user_id == user_id,
                    ),
                )

            query = query.options(
                selectinload(Article.statuses),  # type: ignore
                with_loader_criteria(
                    ArticleStatus,
                    col(ArticleStatus.user_id) == user_id,
                    include_aliases=True,
                ),
                selectinload(Article.feed).selectinload(Feed.subscriptions),  # type: ignore
                with_loader_criteria(
                    FeedSubscription,
                    col(FeedSubscription.user_id) == user_id,
                    include_aliases=True,
                ),
            )

            paginator = (
                self.article_repo.paginate(query=query.stmt)
                .with_params(cursor_params)
                .with_filter(filter_params)
                .with_schema(Article)
            )

            page = await paginator.execute_cursor()

            data = [ArticleOut.from_model(article) for article in page.items]
            metadata = CursorPaginationMetadata.model_validate(page, from_attributes=True)

            return "Articles retrieved successfully", data, metadata
        except Exception as e:
            self.logger.error("Failed to retrieve articles", error=str(e), exc_info=e)
            raise ServiceError("Failed to retrieve articles") from e

    async def get_article(self, user_id: int, article_id: UUID) -> tuple[str, ArticleOut, None]:
        """
        Retrieve a specific article for the specified user.

        Args:
            user_id (int): The ID of the user to retrieve the article for
            article_id (UUID): The ID of the article to retrieve

        Returns:
            tuple[str, ArticleOut, None]: A tuple containing a success message, the retrieved article, and None for metadata

        Raises:
            ServiceError: If the specified article does not exist
        """

        try:
            query = (
                self.article_repo.query()
                .where(col(Article.id) == article_id)
                .outerjoin(
                    ArticleStatus,
                    and_(
                        ArticleStatus.article_id == Article.id,
                        ArticleStatus.user_id == user_id,
                    ),
                )
                .options(
                    contains_eager(Article.statuses),  # type: ignore
                    selectinload(Article.feed).selectinload(Feed.subscriptions),  # type: ignore
                    with_loader_criteria(
                        FeedSubscription,
                        col(FeedSubscription.user_id) == user_id,
                        include_aliases=True,
                    ),
                )
            )

            article = await query.first()

            if not article:
                raise ServiceError("Article not found", status_code=status.HTTP_404_NOT_FOUND)

            return (
                "Article retrieved successfully",
                ArticleOut.from_model(article),
                None,
            )
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to retrieve article",
                article_id=str(article_id),
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to retrieve article") from e

    async def update_article_status(
        self, user_id: int, article_id: UUID, data: ArticleStatusUpdate
    ) -> tuple[str, ArticleStatusOut, None]:
        """
        Update the status of an article for a specific user. If no status exists, it will be created.

        Args:
            user_id (int): The ID of the user to update the article status for
            article_id (UUID): The ID of the article to update the status for
            data (ArticleStatusUpdate): The new status data to apply to the article

        Returns:
            tuple[str, ArticleStatusOut, None]: A tuple containing a success message, the updated article status, and None for metadata

        Raises:
            ServiceError: If the specified article does not exist
        """

        try:
            article = await self.article_repo.get(article_id)
            if not article:
                raise ServiceError("Article not found", status_code=status.HTTP_404_NOT_FOUND)

            article_status = None

            existing_article_status = (
                await self.article_status_repo.query()
                .where(
                    col(ArticleStatus.article_id) == article_id,
                    col(ArticleStatus.user_id) == user_id,
                )
                .first()
            )

            now = datetime.now(UTC)

            update_data = data.model_dump(exclude_unset=True, exclude_none=True)

            if not existing_article_status:
                new_data = {
                    "article_id": article_id,
                    "user_id": user_id,
                    "is_read": False,
                    "is_starred": False,
                    "is_bookmarked": False,
                    **update_data,
                }
                if new_data.get("is_read"):
                    new_data["read_at"] = now
                if new_data.get("is_bookmarked"):
                    new_data["bookmarked_at"] = now

                article_status = await self.article_status_repo.create(new_data)
                await self.article_status_repo.commit()
            else:
                if "is_read" in update_data and update_data["is_read"] != existing_article_status.is_read:
                    update_data["read_at"] = now if update_data["is_read"] else None

                if (
                    "is_bookmarked" in update_data
                    and update_data["is_bookmarked"] != existing_article_status.is_bookmarked
                ):
                    update_data["bookmarked_at"] = now if update_data["is_bookmarked"] else None

                article_status = await self.article_status_repo.update_with_obj(existing_article_status, update_data)

                await self.article_status_repo.commit()

                await self.article_status_repo.refresh(article_status)

                assert article_status is not None

            return (
                "Article status updated successfully",
                ArticleStatusOut.from_model(article_status),
                None,
            )
        except ServiceError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to update article status",
                article_id=str(article_id),
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to update article status") from e

    async def get_article_stats(self, user_id: int) -> tuple[str, ArticleStatsOut, None]:
        """
        Get stats of articles for the authenticated user.

        Args:
            user_id (int): The ID of the user to retrieve stats for.

        Returns:
            tuple[str, ArticleStatsOut, None]: A tuple containing a success message, the stats, and None for metadata.
        """

        try:
            counts = await self.article_repo.get_article_status_counts(user_id)
            return (
                "Article stats retrieved successfully",
                ArticleStatsOut.from_dict(counts),
                None,
            )
        except Exception as e:
            self.logger.error(
                "Failed to retrieve article status counts",
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to retrieve article counts") from e
