from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid7

import pytest

from jobs.feed import FetchFeedJob
from lib.testing import TestJobCase


class TestFetchFeedJob(TestJobCase):

    job_class = FetchFeedJob

    async def test_delegates_to_feed_fetcher_and_delivers_notifications(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "repositories.FeedRepository"
        ) as MockFeedRepo, self.patch("repositories.UserRepository") as MockUserRepo, self.patch(
            "services.feed_fetcher.FeedFetcherService"
        ) as MockFetcher, self.patch(
            "notifiers.PaginationStreamNotification"
        ) as MockPaginationNotification, self.patch(
            "notifiers.NewArticleNotification"
        ) as MockNewArticleNotification:
            MockGetDb.return_value = self.db
            feed = SimpleNamespace(title="Daily News", url="https://example.com/feed")
            user = {"id": 42}

            MockFeedRepo.return_value.get_by = AsyncMock(return_value=feed)
            MockUserRepo.return_value.get_by = AsyncMock(return_value=user)
            feed_id = uuid7()
            MockFetcher.return_value.run = AsyncMock(return_value=(3, 1))
            MockPaginationNotification.return_value.deliver = AsyncMock()
            MockPaginationNotification.return_value.deliver_later = Mock()
            MockNewArticleNotification.return_value.deliver_later = Mock()

            self.make_job().perform(feed_id=feed_id, user_id=42)

        MockFeedRepo.return_value.get_by.assert_called_once_with(id=feed_id)
        MockUserRepo.return_value.get_by.assert_called_once_with(id=42)
        MockFetcher.assert_called_once_with(self.db)
        MockFetcher.return_value.run.assert_awaited_once_with(feed)

        MockPaginationNotification.assert_any_call(dom_id="subscriptions")
        MockPaginationNotification.assert_any_call(dom_id="articles")
        self.assertEqual(MockPaginationNotification.return_value.deliver.call_count, 1)
        MockPaginationNotification.return_value.deliver.assert_awaited_once_with(user)
        MockPaginationNotification.return_value.deliver_later.assert_called_once_with(user)

        MockNewArticleNotification.assert_called_once_with(
            articles_count=3,
            feed_titles=[feed.title],
        )
        MockNewArticleNotification.return_value.deliver_later.assert_called_once_with(user)
        self.db.commit.assert_awaited_once()

    async def test_returns_when_feed_is_missing(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "repositories.FeedRepository"
        ) as MockFeedRepo, self.patch("repositories.UserRepository") as MockUserRepo, self.patch(
            "services.feed_fetcher.FeedFetcherService"
        ) as MockFetcher, self.patch(
            "notifiers.PaginationStreamNotification"
        ) as MockPaginationNotification, self.patch(
            "notifiers.NewArticleNotification"
        ) as MockNewArticleNotification:
            MockGetDb.return_value = self.db
            user = {"id": 42}

            MockFeedRepo.return_value.get_by = AsyncMock(return_value=None)
            MockUserRepo.return_value.get_by = AsyncMock(return_value=user)
            feed_id = uuid7()
            MockFetcher.return_value.run = AsyncMock()
            MockPaginationNotification.return_value.deliver = AsyncMock()
            MockPaginationNotification.return_value.deliver_later = Mock()
            MockNewArticleNotification.return_value.deliver_later = Mock()

            self.make_job().perform(feed_id=feed_id, user_id=42)

        MockFetcher.return_value.run.assert_not_awaited()
        self.db.commit.assert_not_awaited()
        self.assertEqual(MockPaginationNotification.call_count, 0)
        self.assertEqual(MockNewArticleNotification.call_count, 0)

    async def test_raises_when_feed_fetcher_fails(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "repositories.FeedRepository"
        ) as MockFeedRepo, self.patch("repositories.UserRepository") as MockUserRepo, self.patch(
            "services.feed_fetcher.FeedFetcherService"
        ) as MockFetcher:
            MockGetDb.return_value = self.db
            feed = SimpleNamespace(title="Daily News", url="https://example.com/feed")
            user = {"id": 42}

            MockFeedRepo.return_value.get_by = AsyncMock(return_value=feed)
            MockUserRepo.return_value.get_by = AsyncMock(return_value=user)
            feed_id = uuid7()
            MockFetcher.return_value.run = AsyncMock(side_effect=Exception("fetch failed"))

            with pytest.raises(Exception, match="fetch failed"):
                self.make_job().perform(feed_id=feed_id, user_id=42)

        self.db.commit.assert_not_awaited()
