from unittest.mock import AsyncMock, patch

import pytest

from lib.ext.fastapi import ServiceError
from lib.testing.services import TestServiceIntegrationCase
from notifiers import PaginationStreamNotification
from schemas import FolderCreate, FolderUpdate
from services import FolderService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory, FeedSubscriptionFactory, FolderFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestFolderService(TestServiceIntegrationCase):

    service_class = FolderService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_create_folder_persists_folder_and_sends_notification(self) -> None:
        user = await UserFactory.create()

        with patch.object(PaginationStreamNotification, "deliver", new=AsyncMock()) as mock_deliver:
            message = await self.service.create_folder(
                user,
                FolderCreate.model_validate({"name": "Tech News"}),
            )

        assert message == "Folder 'Tech News' created successfully"

        folder = (
            await self.service.folder_repo.query()
            .filter_by(
                user_id=user.id,
                name="Tech News",
            )
            .one_or_none()
        )
        assert folder is not None
        assert folder.user_id == user.id
        assert folder.name == "Tech News"
        mock_deliver.assert_awaited_once_with(user)

    async def test_list_folders_returns_user_folders_and_uncategorized(self) -> None:
        user = await UserFactory.create()
        other_user = await UserFactory.create()

        folder_one = await FolderFactory.create(user=user, name="News")
        await FolderFactory.create(user=user, name="Tech")
        await FolderFactory.create(user=other_user, name="Other")

        message, folders, metadata = await self.service.list_folders(user.id)

        assert message == "Folders retrieved successfully"
        assert metadata is None
        assert len(folders) == 3
        assert any(folder.id == folder_one.id for folder in folders)
        assert any(folder.name == "Uncategorized" and folder.id is None for folder in folders)

    async def test_create_folder_raises_conflict_for_duplicate_name(self) -> None:
        user = await UserFactory.create()
        await FolderFactory.create(user=user, name="Duplicates")

        with pytest.raises(ServiceError) as exc_info:
            await self.service.create_folder(
                user,
                FolderCreate.model_validate({"name": "Duplicates"}),
            )

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value)

    async def test_update_folder_raises_conflict_for_duplicate_name(self) -> None:
        user = await UserFactory.create()
        await FolderFactory.create(user=user, name="First")

        folder_two = await FolderFactory.create(user=user, name="Second")

        with pytest.raises(ServiceError) as exc_info:
            await self.service.update_folder(
                user,
                folder_two.id,
                FolderUpdate.model_validate({"name": "First"}),
            )

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value)

    async def test_delete_folder_clears_subscription_folder_id_and_deletes_folder(
        self,
    ) -> None:
        user = await UserFactory.create()
        folder = await FolderFactory.create(user=user, name="Archive")
        feed = await FeedFactory.create()
        subscription = await FeedSubscriptionFactory.create(user=user, feed=feed, folder=folder)

        with patch.object(PaginationStreamNotification, "deliver", new=AsyncMock()) as mock_deliver:
            message = await self.service.delete_folder(user, folder.id)

        assert message == "Folder deleted successfully"

        refreshed_subscription = (
            await self.service.feed_subscription_repo.query().filter_by(id=subscription.id).one_or_none()
        )
        assert refreshed_subscription is not None
        assert refreshed_subscription.folder_id is None

        deleted_folder = await self.service.folder_repo.query().filter_by(id=folder.id).one_or_none()
        assert deleted_folder is None

        mock_deliver.assert_awaited_once_with(user)
