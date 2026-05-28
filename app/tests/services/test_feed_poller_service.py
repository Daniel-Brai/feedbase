from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from enums import FeedStatus
from lib.testing.services import TestServiceIntegrationCase
from services.feed_poller import FeedPollerService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedPollerService(TestServiceIntegrationCase):

    service_class = FeedPollerService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_run_polls_due_feeds(self) -> None:
        feed = await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=None,
        )

        self.service.feed_fetcher_svc = AsyncMock()
        self.service.feed_fetcher_svc.run = AsyncMock(return_value=(1, 0))

        await self.service.run()

        assert self.service.feed_fetcher_svc.run.await_count == 1
        assert self.service.feed_fetcher_svc.run.await_args.args[0].id == feed.id

    async def test_run_polls_multiple_due_feeds(self) -> None:
        due_feed = await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=None,
        )
        older_feed = await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=datetime.now(UTC) - timedelta(seconds=3600),
        )

        self.service.feed_fetcher_svc = AsyncMock()
        self.service.feed_fetcher_svc.run = AsyncMock(return_value=(0, 0))

        await self.service.run()

        assert self.service.feed_fetcher_svc.run.await_count == 2
        awaited_feed_ids = [call.args[0].id for call in self.service.feed_fetcher_svc.run.await_args_list]
        assert due_feed.id in awaited_feed_ids
        assert older_feed.id in awaited_feed_ids

    async def test_run_continues_when_one_feed_fails(self) -> None:
        failed_feed = await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=None,
        )
        next_feed = await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=datetime.now(UTC) - timedelta(seconds=3600),
        )

        self.service.feed_fetcher_svc = AsyncMock()
        self.service.feed_fetcher_svc.run = AsyncMock(side_effect=[Exception("Failed polling feed"), (1, 0)])
        self.service.db.commit = AsyncMock()

        await self.service.run()

        assert self.service.feed_fetcher_svc.run.await_count == 2
        awaited_feed_ids = [call.args[0].id for call in self.service.feed_fetcher_svc.run.await_args_list]
        assert failed_feed.id in awaited_feed_ids
        assert next_feed.id in awaited_feed_ids
        self.service.db.commit.assert_awaited_once()

    async def test_run_ignores_dead_feeds(self) -> None:
        await FeedFactory.create(
            status=FeedStatus.DEAD,
            last_fetched_at=None,
        )
        active_feed = await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=None,
        )

        self.service.feed_fetcher_svc = AsyncMock()
        self.service.feed_fetcher_svc.run = AsyncMock(return_value=(0, 0))

        await self.service.run()

        assert self.service.feed_fetcher_svc.run.await_count == 1
        assert self.service.feed_fetcher_svc.run.await_args.args[0].id == active_feed.id

    async def test_run_skips_poll_when_no_feeds_due(self) -> None:
        await FeedFactory.create(
            status=FeedStatus.ACTIVE,
            last_fetched_at=datetime.now(UTC),
        )

        self.service.feed_fetcher_svc = AsyncMock()
        self.service.feed_fetcher_svc.run = AsyncMock()

        await self.service.run()

        self.service.feed_fetcher_svc.run.assert_not_awaited()
