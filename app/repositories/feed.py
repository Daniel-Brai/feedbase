from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from enums import FeedStatus
from lib.database import Repository
from models import Feed, FeedSubscription
from settings import settings


class FeedRepository(Repository[Feed, UUID]):
    """
    Repository for managing feeds
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Feed, db)

    async def get_due_feeds(self) -> list[Feed]:
        """
        Retrieves a list of feeds that are due for polling based on their last fetched time and the configured polling interval.

        Returns:
            list[Feed]: A list of Feed objects that are due for polling.
        """

        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=settings.APP_FEED_POLLING_INTERVAL_SECONDS)

        results = (
            await self.query()
            .where(
                col(Feed.status) != FeedStatus.DEAD,
            )
            .or_where(col(Feed.last_fetched_at).is_(None), col(Feed.last_fetched_at) <= cutoff)
            .all()
        )

        return list(results)

    async def get_feeds_by_statuses(self, statuses: list[FeedStatus]) -> list[Feed]:
        """
        Retrieves a list of feeds that match any of the specified statuses.

        Args:
            statuses (list[FeedStatus]): A list of FeedStatus values to filter feeds by.

        Returns:
            list[Feed]: A list of Feed objects that have a status matching any of the specified
            statuses.
        """

        results = await self.query().where(col(Feed.status).in_(statuses)).all()

        return list(results)

    async def get_fever_last_refresh(self, user_id: int) -> int | None:
        """
        Retrieves the timestamp of the last refresh for a user's feeds in the Fever format.

        Args:
            user_id (int): The ID of the user for whom to retrieve the last refresh timestamp

        Returns:
            int | None: The timestamp of the last refresh in seconds since the epoch, or
                         None if there are no feeds with a last fetched time for the user.
        """

        feed = await (
            self.query()
            .join(FeedSubscription, FeedSubscription.feed_id == Feed.id)
            .where(col(FeedSubscription.user_id) == user_id)
            .where(col(Feed.last_fetched_at).isnot(None))
            .order_by(col(Feed.last_fetched_at).desc())
            .first()
        )

        return int(feed.last_fetched_at.timestamp()) if feed and feed.last_fetched_at else None
