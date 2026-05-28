from unittest.mock import ANY, AsyncMock
from uuid import uuid7

import pytest

from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from lib.testing import TestControllerCase
from services import FeedSubscriptionService
from settings import settings
from tests.utils import create_verified_user, get_auth_token, mount_auth_routes

configure_auth()

from controllers.api.v1 import FeedSubscriptionController


@pytest.mark.asyncio
class TestFeedSubscriptionController(TestControllerCase):

    controller_class = FeedSubscriptionController

    async def asyncSetUp(self) -> None:
        configure_controllers()

        await super().asyncSetUp()

        from dependencies.feed import get_feed_subscription_service

        self.feed_subscription_service = AsyncMock(spec=FeedSubscriptionService)
        self.override_dependency(
            get_feed_subscription_service,
            lambda: self.feed_subscription_service,
        )

        mount_auth_routes(self.app)

        self.user = None
        self.auth_cookies = {}

    async def authenticate_user(self) -> None:
        self.user, user_password = await create_verified_user()
        self.auth_cookies = await get_auth_token(self.client, self.user.email, user_password)
        self.client.cookies.update(self.auth_cookies)

    async def test_list_subscribed_feeds_returns_grouped_data(self) -> None:
        await self.authenticate_user()

        folder_id = uuid7()
        subscription_id = uuid7()
        feed_id = uuid7()

        subscription_data = [
            {
                "id": str(folder_id),
                "name": "News",
                "feeds": [
                    {
                        "id": str(subscription_id),
                        "feed_id": str(feed_id),
                        "name": "Example Feed",
                        "url": "https://example.com/rss",
                        "status": "ACTIVE",
                        "last_fetched_at": None,
                    }
                ],
            }
        ]

        self.feed_subscription_service.list_subscribed_feeds.return_value = (
            "Subscriptions retrieved successfully",
            subscription_data,
            {"total": 1},
        )

        response = await self.client.get(f"{settings.API_V1_STR}/subscriptions")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Subscriptions retrieved successfully"
        assert payload["data"] == subscription_data
        assert payload["metadata"]["total"] == 1
        self.feed_subscription_service.list_subscribed_feeds.assert_awaited_once()
        call_args = self.feed_subscription_service.list_subscribed_feeds.call_args[0]

        user = self.user
        assert user is not None
        assert call_args[0] == user.id
        assert call_args[1].size == 10

    async def test_subscribe_to_feeds_calls_service_and_returns_message(self) -> None:
        await self.authenticate_user()

        self.feed_subscription_service.subscribe_to_feeds.return_value = (
            "Feeds subscribed successfully. 1 feed(s) added."
        )

        response = await self.client.post(
            f"{settings.API_V1_STR}/subscriptions",
            json={"urls": ["https://example.com/rss"]},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Feeds subscribed successfully. 1 feed(s) added."
        user = self.user
        assert user is not None
        self.feed_subscription_service.subscribe_to_feeds.assert_awaited_once_with(user.id, ANY)

    async def test_update_subscription_returns_success_for_authenticated_user(
        self,
    ) -> None:
        await self.authenticate_user()

        subscription_id = uuid7()
        self.feed_subscription_service.update_subscription.return_value = "Subscription updated successfully."

        response = await self.client.patch(
            f"{settings.API_V1_STR}/subscriptions/{subscription_id}",
            json={"title": "Updated title"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Subscription updated successfully."
        user = self.user
        assert user is not None
        self.feed_subscription_service.update_subscription.assert_awaited_once_with(user.id, subscription_id, ANY)

    async def test_unsubscribe_from_feed_calls_service_and_returns_message(
        self,
    ) -> None:
        await self.authenticate_user()

        subscription_id = uuid7()
        self.feed_subscription_service.unsubscribe_from_feed.return_value = "Feed unsubscribed successfully."

        response = await self.client.delete(f"{settings.API_V1_STR}/subscriptions/{subscription_id}")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Feed unsubscribed successfully."
        self.feed_subscription_service.unsubscribe_from_feed.assert_awaited_once_with(ANY, subscription_id)

    async def test_refresh_subscriptions_returns_confirmation(self) -> None:
        await self.authenticate_user()

        self.feed_subscription_service.refresh_subscriptions.return_value = (
            "Feed subscriptions refresh initiated successfully."
        )

        response = await self.client.get(f"{settings.API_V1_STR}/subscriptions/refresh")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Feed subscriptions refresh initiated successfully."
        self.feed_subscription_service.refresh_subscriptions.assert_awaited_once_with(ANY)

    async def test_list_subscribed_feeds_returns_401_for_unauthenticated_user(
        self,
    ) -> None:
        response = await self.client.get(f"{settings.API_V1_STR}/subscriptions")

        self.assert_unauthorized(response)
