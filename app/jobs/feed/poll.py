import asyncio

import httpx

from lib.jobs import BaseJob, interval
from settings import settings


class PollFeedJob(BaseJob):
    """
    Feed Polling Job.

    This job is responsible for periodically polling all active feeds in the system to check for updates.

    It runs on a scheduled interval defined by the ``settings.APP_FEED_POLLING_INTERVAL_SECONDS`` setting.

    Also, since it is a recurring job, it is automatically enqueued and will re-enqueue itself after each execution based on the defined schedule.
    """

    queue = "feeds"
    max_attempts = 3
    schedule = interval(seconds=settings.APP_FEED_POLLING_INTERVAL_SECONDS)
    retry_on = (httpx.ConnectError, httpx.TimeoutException, asyncio.TimeoutError)

    def perform(self) -> None:
        """
        Perform the polling of feeds
        """

        async def job_coro() -> None:
            try:
                self.logger.info("PollFeedJob: starting feed polling")

                from bootstrap.database import get_db
                from services.feed_poller import FeedPollerService

                async with get_db() as session:
                    service = FeedPollerService(session)
                    await service.run()

                self.logger.info("PollFeedJob: completed feed polling")
            except Exception as e:
                self.logger.error(f"PollFeedJob: Error occurred while polling feeds - {e}")
                raise e

        self.run_async(job_coro())
