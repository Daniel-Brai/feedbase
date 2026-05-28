from unittest.mock import AsyncMock

import pytest

from enums import FeedStatus
from lib.testing.services import TestServiceIntegrationCase
from services.feed_recovery import FeedRecoveryService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedRecoveryService(TestServiceIntegrationCase):

    service_class = FeedRecoveryService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_run_revives_dead_feed_when_alive(self) -> None:
        dead_feed = await FeedFactory.create(
            url="https://example.com/dead.xml",
            status=FeedStatus.DEAD,
            error_count=3,
            last_error="Failed to fetch",
            last_fetched_at=None,
        )

        self.service._is_feed_alive = AsyncMock(return_value=True)

        await self.service.run()

        refreshed_feed = await self.service.feed_repo.get_by(id=dead_feed.id)
        assert refreshed_feed is not None
        assert refreshed_feed.status == FeedStatus.ACTIVE
        assert refreshed_feed.error_count == 0
        assert refreshed_feed.last_error is None
        assert refreshed_feed.last_fetched_at is not None
        self.service._is_feed_alive.assert_awaited_once_with(dead_feed.url)

    async def test_run_keeps_failing_feed_when_unreachable(self) -> None:
        failing_feed = await FeedFactory.create(
            url="https://example.com/failing.xml",
            status=FeedStatus.FAILING,
            error_count=2,
            last_error="Timeout",
        )

        self.service._is_feed_alive = AsyncMock(return_value=False)

        await self.service.run()

        refreshed_feed = await self.service.feed_repo.get_by(id=failing_feed.id)
        assert refreshed_feed is not None
        assert refreshed_feed.status == FeedStatus.FAILING
        assert refreshed_feed.error_count == 2
        assert refreshed_feed.last_error == "Timeout"
        self.service._is_feed_alive.assert_awaited_once_with(failing_feed.url)

    async def test_run_noop_when_no_dead_or_failing_feeds(self) -> None:
        await FeedFactory.create(status=FeedStatus.ACTIVE)

        self.service._is_feed_alive = AsyncMock()

        await self.service.run()

        assert self.service._is_feed_alive.await_count == 0
