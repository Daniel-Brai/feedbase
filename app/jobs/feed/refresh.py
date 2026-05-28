import asyncio

import httpx

from lib.jobs import BaseJob
from notifiers import PaginationStreamNotification


class RefreshFeedJob(BaseJob):
    """
    Feed Refresh Job.

    This job is responsible for refreshing the feed subscriptions for a user
    """

    queue = "feeds"
    max_attempts = 2
    retry_on = (httpx.ConnectError, httpx.TimeoutException, asyncio.TimeoutError)

    def perform(self, user_id: int) -> None:
        """
        Perform the polling of feeds
        """

        async def job_coro() -> None:
            try:
                self.logger.info("RefreshFeedJob: starting feed refresh")

                from bootstrap.database import get_db
                from repositories.user import UserRepository
                from services.feed_poller import FeedPollerService

                async with get_db() as session:
                    user_repo = UserRepository(session)
                    user = await user_repo.get(user_id)
                    service = FeedPollerService(session)
                    await service.run()

                if user:
                    await PaginationStreamNotification(dom_id="subscriptions").deliver(user)
                    await PaginationStreamNotification(dom_id="articles").deliver(user)

                self.logger.info("RefreshFeedJob: completed feed refresh")
            except Exception as e:
                self.logger.error(f"RefreshFeedJob: Error occurred while refreshing feeds - {e}")
                raise e

        self.run_async(job_coro())
