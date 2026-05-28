from unittest.mock import AsyncMock

import pytest

from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from lib.testing import TestControllerIntegrationCase
from settings import settings
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.utils import create_verified_user, get_auth_token, mount_auth_routes

configure_auth()

from controllers.api.v1 import FeedController


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedController(TestControllerIntegrationCase):

    controller_class = FeedController
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def asyncSetUp(self) -> None:
        configure_controllers()

        await super().asyncSetUp()

        from dependencies.feed import get_feed_discovery_service

        self.feed_discovery_service = AsyncMock()
        self.override_dependency(
            get_feed_discovery_service,
            lambda: self.feed_discovery_service,
        )

        mount_auth_routes(self.app)

        self.user = None
        self.auth_cookies = {}

    async def authenticate_user(self) -> None:
        self.user, user_password = await create_verified_user()
        self.auth_cookies = await get_auth_token(self.client, self.user.email, user_password)
        self.client.cookies.update(self.auth_cookies)

    async def test_discover_feeds_returns_discovered_feeds(self) -> None:
        await self.authenticate_user()

        discovered_feeds = [{"value": "https://example.com/rss", "text": "Example Feed"}]
        self.feed_discovery_service.run.return_value = (
            "Feeds discovered successfully",
            discovered_feeds,
            None,
        )

        response = await self.client.post(
            f"{settings.API_V1_STR}/feeds/discover",
            json={"url": "https://example.com/rss"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Feeds discovered successfully"
        assert payload["data"] == discovered_feeds
        assert payload["metadata"] is None
        self.feed_discovery_service.run.assert_awaited_once()

    async def test_discover_feeds_returns_422_for_invalid_payload(self) -> None:
        await self.authenticate_user()

        response = await self.client.post(
            f"{settings.API_V1_STR}/feeds/discover",
            json={"url": 123},
        )

        assert response.status_code == 422
        payload = response.json()
        assert payload["detail"][0]["loc"] == ["body", "url", "str"]
        assert payload["detail"][0]["type"] == "string_type"

    async def test_discover_feeds_returns_401_for_unauthenticated_user(self) -> None:
        response = await self.client.post(
            f"{settings.API_V1_STR}/feeds/discover",
            json={"url": "https://example.com/rss"},
        )

        self.assert_unauthorized(response)
