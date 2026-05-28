from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import and_, case, col, delete, func, not_, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lib.database import Repository
from models import Article, ArticleStatus, Feed, FeedSubscription


class ArticleRepository(Repository[Article, UUID]):
    """
    Repository for managing articles
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Article, db)

    async def get_all_articles_for_feed(self, feed_id: UUID) -> list[Article]:
        """
        Get all articles for a given feed
        """
        results = await self.query().where(col(Article.feed_id) == feed_id).all()

        return list(results)

    async def fetch_unread_articles(
        self,
        user_id: int,
        cutoff: datetime,
        now: datetime,
    ) -> list[Article]:
        """
        Fetch unread articles from feeds the user subscribes to that are published between `cutoff` and `now`.

        Args:
            user_id (int): The ID of the user.
            cutoff (datetime): The earliest publication date of articles to include.
            now (datetime): The latest publication date of articles to include.

        Returns:
            list[Article]: A list of unread articles for the user.
        """

        results = await (
            self.query()
            .options(selectinload(Article.feed))  # type: ignore
            .join(Feed, col(Feed.id) == col(Article.feed_id))
            .join(FeedSubscription, col(FeedSubscription.feed_id) == col(Feed.id))
            .where(
                col(FeedSubscription.user_id) == user_id,
                col(Article.published_at) >= cutoff,
                col(Article.published_at) <= now,
            )
            .outerjoin(
                ArticleStatus,
                and_(
                    col(ArticleStatus.article_id) == col(Article.id),
                    col(ArticleStatus.user_id) == user_id,
                ),
            )
            .where(
                or_(
                    col(ArticleStatus.id).is_(None),
                    col(ArticleStatus.is_read) == False,
                )
            )
            .order_by(col(Article.published_at).desc())
            .all()
        )

        return list(results)

    async def delete_old_unstarred_unbookmarked_articles(self, cutoff: datetime) -> int:
        """
        Delete articles older than `cutoff` that are neither starred, bookmarked nor read by any user.

        Args:
            cutoff (datetime): Articles with `published_at` older than this timestamp are candidates.

        Returns:
            int: Number of articles permanently deleted.
        """

        keep_article_subq = (
            select(ArticleStatus.article_id)
            .where(
                or_(
                    col(ArticleStatus.is_read) == False,
                    col(ArticleStatus.is_starred) == True,
                    col(ArticleStatus.is_bookmarked) == True,
                )
            )
            .subquery()
        )

        articles_to_delete_subq = (
            select(Article.id)
            .where(
                col(Article.published_at).is_not(None),
                col(Article.published_at) < cutoff,
                not_(col(Article.id).in_(keep_article_subq)),  # type: ignore[operator]
            )
            .subquery()
        )

        delete_status_stmt = delete(ArticleStatus).where(
            col(ArticleStatus.article_id).in_(articles_to_delete_subq)  # type: ignore[operator]
        )
        await self.db.exec(delete_status_stmt)

        delete_article_stmt = delete(Article).where(
            col(Article.id).in_(articles_to_delete_subq)  # type: ignore[operator]
        )
        result = await self.db.exec(delete_article_stmt)
        await self.db.flush()

        return result.rowcount

    async def get_fever_articles(
        self,
        user_id: int,
        limit: int,
        with_ids_list: list[int] | None = None,
        since_id: int | None = None,
        max_id: int | None = None,
    ) -> list[Article]:
        """
        Get articles for Fever API, filtered by user subscriptions and optional ID parameters.

        Args:
            user_id (int): The ID of the user.
            limit (int): Maximum number of articles to return.
            with_ids_list (list[int] | None): Optional list of article IDs to include.
            since_id (int | None): Optional article ID; only return articles with ID greater than this.
            max_id (int | None): Optional article ID; only return articles with ID less than this.

        Returns:
            list[Article]: A list of articles matching the criteria.
        """

        stmt = (
            self.query()
            .join(FeedSubscription, col(FeedSubscription.feed_id) == col(Article.feed_id))
            .where(col(FeedSubscription.user_id) == user_id)
            .order_by(col(Article.id).desc())
            .limit(limit)
        )

        if with_ids_list:
            stmt = stmt.where(col(Article.id).in_([UUID(int=i) for i in with_ids_list]))
        elif since_id is not None:
            stmt = stmt.where(col(Article.id) > UUID(int=since_id))
        elif max_id is not None:
            stmt = stmt.where(col(Article.id) < UUID(int=max_id))

        results = await stmt.all()

        return list(results)

    async def get_unread_article_ids(self, user_id: int) -> list[UUID]:
        """
        Get a list of article IDs that are unread for the given user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[UUID]: A list of article IDs that are unread for the user.
        """

        articles = await (
            self.query()
            .join(FeedSubscription, col(FeedSubscription.feed_id) == col(Article.feed_id))
            .outerjoin(
                ArticleStatus,
                and_(
                    col(ArticleStatus.article_id) == col(Article.id),
                    col(ArticleStatus.user_id) == user_id,
                ),
            )
            .where(col(FeedSubscription.user_id) == user_id)
            .where(or_(col(ArticleStatus.id).is_(None), col(ArticleStatus.is_read) == False))
            .all()
        )

        return [article.id for article in articles]

    async def get_saved_article_ids(self, user_id: int) -> list[UUID]:
        """
        Get a list of article IDs that are saved for the given user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[UUID]: A list of article IDs that are saved for the user.
        """

        articles = await (
            self.query()
            .join(FeedSubscription, col(FeedSubscription.feed_id) == col(Article.feed_id))
            .join(
                ArticleStatus,
                and_(
                    col(ArticleStatus.article_id) == col(Article.id),
                    col(ArticleStatus.user_id) == user_id,
                ),
            )
            .where(
                col(FeedSubscription.user_id) == user_id,
                col(ArticleStatus.is_starred) == True,
            )
            .all()
        )

        return [article.id for article in articles]

    async def get_article_status_counts(self, user_id: int) -> dict[str, int]:
        """
        Get the counts of different article statuses for the given user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            dict[str, int]: A dictionary containing counts for total, unread, starred, bookmarked, and today's articles.
        """

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(
                func.count(col(Article.id)).label("total"),
                func.sum(
                    case(
                        (
                            or_(
                                col(ArticleStatus.id).is_(None),
                                col(ArticleStatus.is_read) == False,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("unread"),
                func.sum(case((col(ArticleStatus.is_starred) == True, 1), else_=0)).label("starred"),
                func.sum(case((col(ArticleStatus.is_bookmarked) == True, 1), else_=0)).label("bookmarked"),
                func.sum(case((col(Article.published_at) >= today_start, 1), else_=0)).label("today"),
            )  # type: ignore
            .join(FeedSubscription, col(FeedSubscription.feed_id) == col(Article.feed_id))
            .outerjoin(
                ArticleStatus,
                and_(
                    col(ArticleStatus.article_id) == col(Article.id),
                    col(ArticleStatus.user_id) == user_id,
                ),
            )
            .where(col(FeedSubscription.user_id) == user_id)
        )

        result = await self.db.exec(query)
        row = result.first()

        if not row:
            return {"total": 0, "unread": 0, "starred": 0, "bookmarked": 0, "today": 0}

        return {
            "total": int(getattr(row, "total", 0) or 0),
            "unread": int(getattr(row, "unread", 0) or 0),
            "starred": int(getattr(row, "starred", 0) or 0),
            "bookmarked": int(getattr(row, "bookmarked", 0) or 0),
            "today": int(getattr(row, "today", 0) or 0),
        }
