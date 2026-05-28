from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import col, select

from bootstrap.auth import configure_auth

configure_auth()

from bootstrap.controllers import configure_controllers
from controllers.api.v1 import FolderController
from lib.testing import TestControllerIntegrationCase
from models import FeedSubscription, Folder
from services import FolderService
from settings import settings
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory, FeedSubscriptionFactory, FolderFactory
from tests.utils import create_verified_user, get_auth_token, mount_auth_routes


@pytest.mark.integration
@pytest.mark.asyncio
class TestFolderController(TestControllerIntegrationCase):

    controller_class = FolderController
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def asyncSetUp(self) -> None:
        configure_controllers()

        await super().asyncSetUp()

        from dependencies.folder import get_folder_service

        self.override_dependency(
            get_folder_service,
            lambda: FolderService(self.db),
        )

        mount_auth_routes(self.app)

        self.user: Any = None
        self.auth_cookies = {}

    async def authenticate_user(self) -> None:
        self.user, user_password = await create_verified_user()
        self.auth_cookies = await get_auth_token(self.client, self.user.email, user_password)
        self.client.cookies.update(self.auth_cookies)

    async def test_list_folders_returns_user_folders_and_uncategorized(self) -> None:
        await self.authenticate_user()

        folder = await FolderFactory.create(user=self.user, name="News")

        response = await self.client.get(f"{settings.API_V1_STR}/folders")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Folders retrieved successfully"
        assert any(item["id"] == str(folder.id) and item["name"] == "News" for item in payload["data"])
        assert any(item["id"] is None and item["name"] == "Uncategorized" for item in payload["data"])

    async def test_create_folder_creates_folder_and_returns_message(self) -> None:
        await self.authenticate_user()

        with patch("services.folder.PaginationStreamNotification.deliver", new=AsyncMock()) as mock_deliver:
            response = await self.client.post(
                f"{settings.API_V1_STR}/folders",
                json={"name": "Tech News"},
            )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Folder 'Tech News' created successfully"

        result = await self.db.exec(
            select(Folder).where(col(Folder.user_id) == self.user.id, col(Folder.name) == "Tech News")  # type: ignore
        )  # type: ignore
        created_folder = result.one_or_none()

        assert created_folder is not None
        assert created_folder.name == "Tech News"
        assert mock_deliver.await_count == 1
        assert mock_deliver.await_args is not None
        assert mock_deliver.await_args.args[0].id == self.user.id

    async def test_update_folder_updates_name_and_returns_success(self) -> None:
        await self.authenticate_user()

        folder = await FolderFactory.create(user=self.user, name="Old Name")

        with patch("services.folder.PaginationStreamNotification.deliver", new=AsyncMock()) as mock_deliver:
            response = await self.client.patch(
                f"{settings.API_V1_STR}/folders/{folder.id}",
                json={"name": "New Name"},
            )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Folder updated successfully"

        result = await self.db.exec(select(Folder).where(col(Folder.id) == folder.id))  # type: ignore
        updated_folder = result.one()

        assert updated_folder.name == "New Name"
        assert mock_deliver.await_count == 1
        assert mock_deliver.await_args is not None
        assert mock_deliver.await_args.args[0].id == self.user.id

    async def test_delete_folder_clears_subscriptions_and_returns_success(self) -> None:
        await self.authenticate_user()

        folder = await FolderFactory.create(user=self.user, name="Archive")
        feed = await FeedFactory.create()
        subscription = await FeedSubscriptionFactory.create(user=self.user, feed=feed, folder=folder)

        with patch("services.folder.PaginationStreamNotification.deliver", new=AsyncMock()) as mock_deliver:
            response = await self.client.delete(f"{settings.API_V1_STR}/folders/{folder.id}")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Folder deleted successfully"

        sub_result = await self.db.exec(
            select(FeedSubscription).where(col(FeedSubscription.id) == subscription.id)  # type: ignore
        )
        refreshed_subscription = sub_result.one()

        assert refreshed_subscription.folder_id is None
        assert mock_deliver.await_count == 1
        assert mock_deliver.await_args is not None
        assert mock_deliver.await_args.args[0].id == self.user.id

    async def test_list_folders_returns_401_for_unauthenticated_user(self) -> None:
        response = await self.client.get(f"{settings.API_V1_STR}/folders")

        self.assert_unauthorized(response)
