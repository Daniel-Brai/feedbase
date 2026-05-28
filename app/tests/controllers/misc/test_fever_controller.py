import pytest

from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers

configure_auth()

from controllers.misc.fever import FeverController
from lib.testing import TestControllerIntegrationCase
from models import User
from services import FeverService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import (
    ArticleFactory,
    ArticleStatusFactory,
    FeedFactory,
    FeedSubscriptionFactory,
    FolderFactory,
    UserFactory,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeverController(TestControllerIntegrationCase):

    controller_class = FeverController
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def asyncSetUp(self) -> None:
        configure_controllers()

        await super().asyncSetUp()

        from dependencies.fever import get_fever_service

        self.override_dependency(
            get_fever_service,
            lambda: FeverService(self.db),
        )

    async def test_handle_request_returns_items_and_status_ids(self) -> None:
        user = await UserFactory.create(email_verified=True)

        feed = await FeedFactory.create(
            url="https://example.org/rss",
            title="Example Feed",
            site_url="https://example.org",
        )

        await FeedSubscriptionFactory.create(user=user, feed=feed)

        unread_article = await ArticleFactory.create(
            feed=feed,
            guid="unread-article-guid",
            title="Unread article",
        )
        saved_article = await ArticleFactory.create(
            feed=feed,
            guid="saved-article-guid",
            title="Saved article",
        )

        await ArticleStatusFactory.create(
            user=user,
            article=saved_article,
            is_read=False,
            is_starred=True,
        )

        response = await self.client.post(
            "/fever",
            params={
                "api": "true",
                "items": "true",
                "unread_item_ids": "true",
                "saved_item_ids": "true",
            },
            data={
                "api_key": user.fever_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["auth"] == 1
        assert payload["total_items"] == 2
        assert payload["items"] is not None
        assert {item["id"] for item in payload["items"]} == {
            unread_article.id.int,
            saved_article.id.int,
        }
        assert {int(value) for value in payload["unread_item_ids"].split(",")} == {
            unread_article.id.int,
            saved_article.id.int,
        }
        assert {int(value) for value in payload["saved_item_ids"].split(",")} == {
            saved_article.id.int,
        }

    async def test_handle_request_returns_auth_zero_for_invalid_api_key(self) -> None:
        response = await self.client.post(
            "/fever",
            params={
                "api": "true",
                "items": "true",
            },
            data={"api_key": "invalid-key"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["auth"] == 0
        assert payload.get("items") is None
        assert payload.get("total_items") is None

    async def test_handle_request_returns_groups_for_user_folders(self) -> None:
        user = await UserFactory.create(email_verified=True)

        feed = await FeedFactory.create(
            url="https://example.org/grouped",
            title="Grouped Feed",
            site_url="https://example.org/grouped",
        )
        folder = await FolderFactory.create(user=user, name="News")
        await FeedSubscriptionFactory.create(user=user, feed=feed, folder=folder)

        response = await self.client.post(
            "/fever",
            params={
                "api": "true",
                "groups": "true",
            },
            data={
                "api_key": user.fever_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["auth"] == 1
        assert payload["groups"] is not None
        assert any(group["title"] == "Uncategorised" for group in payload["groups"])
        assert any(group["id"] == folder.id.int and group["title"] == "News" for group in payload["groups"])

    async def test_handle_login_sets_fever_auth_cookie(self) -> None:
        user = await UserFactory.create(email_verified=True, fever_key=None)

        response = await self.client.post(
            "/fever",
            params={"action": "login"},
            data={
                "username": user.email,
                "password": "password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["auth"] == 1
        assert response.cookies.get("fever_auth") is not None

        updated_user = await self.db.get(User, user.id)
        assert updated_user is not None
        assert response.cookies["fever_auth"] == updated_user.fever_key
