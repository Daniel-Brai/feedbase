from typing import Any

import pytest

from bootstrap.auth import configure_auth

configure_auth()

from bootstrap.controllers import configure_controllers
from controllers.api.v1 import UserController
from lib.testing import TestControllerIntegrationCase
from models import User
from services import UserService
from settings import settings
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.utils import create_verified_user, get_auth_token, mount_auth_routes


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserController(TestControllerIntegrationCase):

    controller_class = UserController
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def asyncSetUp(self) -> None:
        configure_controllers()

        await super().asyncSetUp()

        from dependencies.user import get_user_service

        self.override_dependency(
            get_user_service,
            lambda: UserService(self.db),
        )

        mount_auth_routes(self.app)

        self.user: Any = None
        self.auth_cookies = {}

    async def authenticate_user(self) -> None:
        self.user, user_password = await create_verified_user()
        self.auth_cookies = await get_auth_token(self.client, self.user.email, user_password)
        self.client.cookies.update(self.auth_cookies)
        assert self.user is not None

    async def test_update_profile_updates_name_and_bio(self) -> None:
        await self.authenticate_user()

        response = await self.client.patch(
            f"{settings.API_V1_STR}/accounts/me",
            json={"name": "Updated Name", "bio": "Updated bio"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Profile updated successfully."
        assert payload["data"]["name"] == "Updated Name"
        assert payload["data"]["bio"] == "Updated bio"

        refreshed_user = await self.db.get(User, self.user.id)
        assert refreshed_user is not None
        assert refreshed_user.name == "Updated Name"
        assert refreshed_user.bio == "Updated bio"

    async def test_update_preferences_merges_preferences(self) -> None:
        await self.authenticate_user()

        response = await self.client.patch(
            f"{settings.API_V1_STR}/accounts/me/preferences",
            json={"digest_frequency": "weekly", "allow_push_notifications": True},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Preferences updated successfully."
        assert payload["data"]["preferences"]["digest_frequency"] == "weekly"
        assert payload["data"]["preferences"]["allow_push_notifications"] is True

        refreshed_user = await self.db.get(User, self.user.id)
        assert refreshed_user is not None
        assert refreshed_user.preferences["digest_frequency"] == "weekly"
        assert refreshed_user.preferences["allow_push_notifications"] is True

    async def test_update_profile_returns_401_for_unauthenticated_user(self) -> None:
        response = await self.client.patch(
            f"{settings.API_V1_STR}/accounts/me",
            json={"name": "Should Not Update"},
        )

        self.assert_unauthorized(response)
