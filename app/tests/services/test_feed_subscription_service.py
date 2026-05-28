from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid7

import pytest

from jobs import FetchFeedJob, RefreshFeedJob
from lib.ext.fastapi import ServiceError
from lib.pagination import CursorParams
from lib.testing.services import TestServiceIntegrationCase
from notifiers import PaginationStreamNotification
from schemas import FeedSubscriptionCreate, FeedSubscriptionUpdate
from services import FeedSubscriptionService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory, FeedSubscriptionFactory, FolderFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedSubscriptionService(TestServiceIntegrationCase):

    service_class = FeedSubscriptionService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_subscribe_to_new_feed_creates_feed_and_subscription(self) -> None:
        user = await UserFactory.create()
        body = FeedSubscriptionCreate(urls=["https://example.org/rss"])

        with patch.object(FetchFeedJob, "perform_later", new=Mock()) as mock_perform:
            message = await self.service.subscribe_to_feeds(user.id, body)

        assert "1 feed(s) added" in message
        assert mock_perform.called

        feed = await self.service.feed_repo.query().filter_by(url="https://example.org/rss").one_or_none()
        assert feed is not None

        subscriptions = await self.service.feed_subscription_repo.query().filter_by(user_id=user.id).all()
        assert len(subscriptions) == 1

    async def test_subscribe_reuses_existing_feed_when_url_exists(self) -> None:
        user = await UserFactory.create()
        existing_feed = await FeedFactory.create(url="https://example.org/reuse.xml")

        with patch.object(FetchFeedJob, "perform_later", new=Mock()) as mock_perform:
            message = await self.service.subscribe_to_feeds(user.id, FeedSubscriptionCreate(urls=[existing_feed.url]))

        assert "1 feed(s) added" in message
        assert mock_perform.called

        subscriptions = await self.service.feed_subscription_repo.query().filter_by(user_id=user.id).all()
        assert len(subscriptions) == 1
        assert subscriptions[0].feed_id == existing_feed.id

    async def test_subscribe_to_duplicate_feed_returns_already_subscribed(self) -> None:
        user = await UserFactory.create()
        url = "https://example.org/duplicate.xml"

        with patch.object(FetchFeedJob, "perform_later", new=Mock()):
            await self.service.subscribe_to_feeds(user.id, FeedSubscriptionCreate(urls=[url]))

        with patch.object(FetchFeedJob, "perform_later", new=Mock()) as mock_perform:
            message = await self.service.subscribe_to_feeds(user.id, FeedSubscriptionCreate(urls=[url]))

        assert message == "You are already subscribed to the provided feed(s)."
        assert not mock_perform.called

        subscription_rows = await self.service.feed_subscription_repo.query().filter_by(user_id=user.id).all()
        assert len(subscription_rows) == 1

    async def test_list_subscribed_feeds_groups_by_folder_and_uncategorized(
        self,
    ) -> None:
        user = await UserFactory.create()
        folder = await FolderFactory.create(user=user, name="News")
        feed_a = await FeedFactory.create(url="https://example.org/news.xml", title="News Feed")
        feed_b = await FeedFactory.create(url="https://example.org/uncategorized.xml", title="Uncategorized Feed")

        await FeedSubscriptionFactory.create(user=user, feed=feed_a, folder=folder)
        await FeedSubscriptionFactory.create(user=user, feed=feed_b)

        message, data, metadata = await self.service.list_subscribed_feeds(
            user.id,
            CursorParams(),
        )

        assert message == "Subscriptions retrieved successfully"
        assert metadata.total == 2
        assert any(folder_item.name == "News" for folder_item in data)
        assert any(folder_item.name == "Uncategorized" for folder_item in data)

        news_folder = next(item for item in data if item.name == "News")
        assert len(news_folder.feeds) == 1
        assert news_folder.feeds[0].name == "News Feed"

        uncategorized = next(item for item in data if item.name == "Uncategorized")
        assert len(uncategorized.feeds) == 1
        assert uncategorized.feeds[0].name == "Uncategorized Feed"

    async def test_update_subscription_title_and_folder_is_persisted(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        folder = await FolderFactory.create(user=user, name="Books")
        subscription = await FeedSubscriptionFactory.create(user=user, feed=feed, title="Old")

        result = await self.service.update_subscription(
            user.id,
            subscription.id,
            FeedSubscriptionUpdate.model_validate({"title": "Updated title", "folder_id": folder.id}),
        )

        assert result == "Subscription updated successfully."

        updated_subscription = (
            await self.service.feed_subscription_repo.query().filter_by(id=subscription.id).one_or_none()
        )
        assert updated_subscription is not None
        assert updated_subscription.title == "Updated title"
        assert updated_subscription.folder_id == folder.id

    async def test_update_subscription_with_none_title_does_not_clear_title(
        self,
    ) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        folder = await FolderFactory.create(user=user, name="Tech")
        subscription = await FeedSubscriptionFactory.create(user=user, feed=feed, title="Keep Me", folder=folder)

        result = await self.service.update_subscription(
            user.id,
            subscription.id,
            FeedSubscriptionUpdate.model_validate({"title": None, "folder_id": folder.id}),
        )

        assert result == "Subscription updated successfully."

        refreshed_subscription = (
            await self.service.feed_subscription_repo.query().filter_by(id=subscription.id).one_or_none()
        )
        assert refreshed_subscription is not None
        assert refreshed_subscription.title == "Keep Me"
        assert refreshed_subscription.folder_id == folder.id

    async def test_update_subscription_missing_subscription_raises_not_found(
        self,
    ) -> None:
        user = await UserFactory.create()
        unknown_id = uuid7()

        with pytest.raises(ServiceError) as exc_info:
            await self.service.update_subscription(
                user.id,
                unknown_id,
                FeedSubscriptionUpdate.model_validate({"title": "x"}),
            )

        assert exc_info.value.status_code == 404
        assert "Subscription not found" in str(exc_info.value)

    async def test_unsubscribe_from_feed_removes_subscription_and_sends_notification(
        self,
    ) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        subscription = await FeedSubscriptionFactory.create(user=user, feed=feed)

        with patch.object(PaginationStreamNotification, "deliver", new=AsyncMock()) as mock_deliver:
            message = await self.service.unsubscribe_from_feed(user, subscription.id)

        assert message == "Feed unsubscribed successfully."
        assert mock_deliver.called

        remaining = await self.service.feed_subscription_repo.query().filter_by(id=subscription.id).one_or_none()
        assert remaining is None

    async def test_unsubscribe_from_nonexistent_subscription_raises_not_found(
        self,
    ) -> None:
        user = await UserFactory.create()
        orphan_id = uuid7()

        with pytest.raises(ServiceError) as exc_info:
            await self.service.unsubscribe_from_feed(user, orphan_id)

        assert exc_info.value.status_code == 404
        assert "Subscription not found" in str(exc_info.value)

    async def test_refresh_subscriptions_dispatches_refresh_job(self) -> None:
        user = await UserFactory.create()

        with patch.object(RefreshFeedJob, "perform_later", new=Mock()) as mock_refresh:
            message = await self.service.refresh_subscriptions(user)

        assert message == "Feed subscriptions refresh initiated successfully."
        mock_refresh.assert_called_once_with(user_id=user.id)
