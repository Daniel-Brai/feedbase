import asyncio
from typing import Any
from uuid import UUID

import httpx

from lib.jobs import BaseJob


class FetchFeedJob(BaseJob):
    """
    Feed Fetching Job.

    This job is responsible for fetching and parsing feeds and its articles from URLs.
    """

    queue = "feeds"
    max_attempts = 3
    retry_on = (httpx.ConnectError, httpx.TimeoutException, asyncio.TimeoutError)

    def perform(self, feed_id: UUID, user_id: int) -> None:
        """
        Perform the feed fetching and parsing.
        """

        async def job_coro() -> None:
            try:
                self.logger.info(f"FetchFeedJob: starting feed fetch feed_id = {feed_id}, user_id = {user_id}")

                from bootstrap.database import get_db
                from notifiers import NewArticleNotification, PaginationStreamNotification
                from repositories import FeedRepository, UserRepository
                from services.feed_fetcher import FeedFetcherService

                async with get_db() as session:
                    feed_repo = FeedRepository(session)
                    user_repo = UserRepository(session)
                    feed = await feed_repo.get_by(id=feed_id)
                    user = await user_repo.get_by(id=user_id)
                    if not feed or not user:
                        self.logger.error(f"FetchFeedJob: Feed with id {feed_id} or user with id {user_id} not found")
                        return

                    service = FeedFetcherService(session)
                    new_articles_count, _ = await service.run(feed)

                    await session.commit()

                await PaginationStreamNotification(dom_id="subscriptions").deliver(user)

                PaginationStreamNotification(dom_id="articles").deliver_later(user)

                if new_articles_count > 0 and feed and feed.title:
                    NewArticleNotification(articles_count=new_articles_count, feed_titles=[feed.title]).deliver_later(
                        user
                    )

                self.logger.info(f"FetchFeedJob: completed feed fetch for {feed.url}")
            except Exception as e:
                self.logger.error(f"FetchFeedJob: Error occurred while fetching feed feed_id = {feed_id}, - {e}")
                raise e

        self.run_async(job_coro())

    @classmethod
    def perform_later(cls, feed_id: UUID, user_id: int, **kwargs: Any):
        return super().perform_later(feed_id, user_id=user_id, **kwargs)
