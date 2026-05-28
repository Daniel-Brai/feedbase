from sqlmodel.ext.asyncio.session import AsyncSession

from lib.ext.fastapi import IORunnableService
from repositories import FeedRepository
from services.feed_fetcher import FeedFetcherService


class FeedPollerService(IORunnableService):
    """
    Service for polling feeds
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.feed_repo = FeedRepository(db)
        self.feed_fetcher_svc = FeedFetcherService(db)

    async def run(self) -> None:
        """
        Main entry point to run the feed poller.

        This method will fetch all due feeds and process them accordingly.
        """

        await self._poll_due_feeds()

    async def _poll_due_feeds(self) -> None:
        due_feeds = await self.feed_repo.get_due_feeds()
        if not due_feeds:
            self.logger.info("No feeds are due for polling at this time.")
            return

        self.logger.info(f"Polling {len(due_feeds)} due feeds...")
        for feed in due_feeds:
            try:
                await self.feed_fetcher_svc.run(feed)
            except Exception as e:
                self.logger.error(f"Error polling feed {feed.url}: {e}")

        await self.db.commit()
