from datetime import UTC, datetime

import httpx
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from enums import FeedStatus
from lib.ext.fastapi import IORunnableService
from repositories import FeedRepository


class FeedRecoveryService(IORunnableService):
    """
    Service for recovering dead or failing feeds by checking if they become reachable again.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.feed_repo = FeedRepository(db)

    async def run(self) -> None:
        """
        Main entry point for the feed recovery process.

        This method will check all feeds marked as DEAD or FAILING and attempt to recover them if they become reachable again.
        """

        feeds = await self.feed_repo.get_feeds_by_statuses([FeedStatus.DEAD, FeedStatus.FAILING])
        if not feeds:
            self.logger.info("No dead or failing feeds to recover.")
            return

        self.logger.info(f"Attempting to recover {len(feeds)} feeds...")
        for feed in feeds:
            try:
                if await self._is_feed_alive(feed.url):
                    await self.feed_repo.update_with_obj(
                        feed,
                        {
                            "status": FeedStatus.ACTIVE,
                            "error_count": 0,
                            "last_error": None,
                            "last_fetched_at": datetime.now(UTC),
                        },
                    )
                    self.logger.info(f"Revived feed: {feed.url}")
                else:
                    self.logger.debug(f"Feed still unreachable: {feed.url}")
            except Exception as e:
                self.logger.error(f"Error checking feed {feed.url}: {e}")

    async def _is_feed_alive(self, url: str) -> bool:
        """
        Performs a lightweight HTTP check to see if the feed is reachable.
        """
        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.head(url)
                if response.status_code < status.HTTP_400_BAD_REQUEST:
                    return True

                if response.status_code in (
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                    status.HTTP_501_NOT_IMPLEMENTED,
                    status.HTTP_400_BAD_REQUEST,
                ):
                    headers = {"Range": "bytes=0-1023"}
                    response = await client.get(url, headers=headers)
                    if (
                        response.status_code in (status.HTTP_200_OK, status.HTTP_206_PARTIAL_CONTENT)
                        and response.status_code < status.HTTP_400_BAD_REQUEST
                    ):
                        return True

                return False
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            self.logger.debug(f"Health check failed for {url}: {e}")
            return False
