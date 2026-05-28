import pytest

from lib.testing.services import TestServiceIntegrationCase
from schemas import UserPreferencesUpdate, UserProfileUpdate
from services.user import UserService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserService(TestServiceIntegrationCase):

    service_class = UserService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_update_profile_updates_only_provided_fields(self) -> None:
        user = await UserFactory.create(name="Original Name", bio="Original biography")

        user = await self.service.user_repo.get(user.id)

        message, user_out, metadata = await self.service.update_profile(
            user,
            UserProfileUpdate.model_validate(
                {
                    "name": "Updated Name",
                }
            ),
        )

        assert message == "Profile updated successfully."
        assert metadata is None
        assert user_out.name == "Updated Name"
        assert user_out.bio == "Original biography"

        refreshed_user = await self.service.user_repo.query().filter_by(id=user.id).one_or_none()
        assert refreshed_user is not None
        assert refreshed_user.name == "Updated Name"
        assert refreshed_user.bio == "Original biography"

    async def test_update_preferences_merges_existing_preferences(self) -> None:
        user = await UserFactory.create(
            preferences={
                "digest_frequency": "weekly",
                "digest_hour": 8,
                "allow_push_notifications": True,
                "mark_article_as_unread_if_updated": False,
            }
        )
        user = await self.service.user_repo.get(user.id)

        message, user_out, metadata = await self.service.update_preferences(
            user,
            UserPreferencesUpdate.model_validate(
                {
                    "digest_hour": 22,
                    "allow_push_notifications": False,
                }
            ),
        )

        assert message == "Preferences updated successfully."
        assert metadata is None
        assert user_out.preferences["digest_frequency"] == "weekly"
        assert user_out.preferences["digest_hour"] == 22
        assert user_out.preferences["allow_push_notifications"] is False
        assert user_out.preferences["mark_article_as_unread_if_updated"] is False

        refreshed_user = await self.service.user_repo.query().filter_by(id=user.id).one_or_none()
        assert refreshed_user is not None
        assert refreshed_user.preferences["digest_frequency"] == "weekly"
        assert refreshed_user.preferences["digest_hour"] == 22
        assert refreshed_user.preferences["allow_push_notifications"] is False

    async def test_update_preferences_initializes_missing_preferences(self) -> None:
        user = await UserFactory.create(preferences={})
        user = await self.service.user_repo.get(user.id)

        message, user_out, metadata = await self.service.update_preferences(
            user,
            UserPreferencesUpdate.model_validate(
                {
                    "digest_frequency": "daily",
                }
            ),
        )

        assert message == "Preferences updated successfully."
        assert metadata is None
        assert user_out.preferences["digest_frequency"] == "daily"
        assert user_out.preferences["digest_hour"] == 0
        assert user_out.preferences["allow_push_notifications"] is False
        assert user_out.preferences["mark_article_as_unread_if_updated"] is False

        refreshed_user = await self.service.user_repo.query().filter_by(id=user.id).one_or_none()
        assert refreshed_user is not None
        assert refreshed_user.preferences["digest_frequency"] == "daily"
        assert refreshed_user.preferences["digest_hour"] == 0
        assert refreshed_user.preferences["allow_push_notifications"] is False
        assert refreshed_user.preferences["mark_article_as_unread_if_updated"] is False
