from datetime import UTC, datetime

import pytest

from bootstrap.auth import configure_auth

configure_auth()

from lib.testing.services import TestServiceIntegrationCase
from schemas import FeverForm, FeverQuery
from services.fever import FeverService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeverService(TestServiceIntegrationCase):

    service_class = FeverService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_handle_request_returns_fever_items_and_status_ids(self) -> None:
        user = await UserFactory.create()
        user = await self.service.user_repo.get(user.id)

        feed = await FeedFactory.create(
            url="https://example.org/rss",
            title="Example Feed",
            site_url="https://example.org",
        )

        await self.service.feed_subscription_repo.create(
            {
                "user_id": user.id,
                "feed_id": feed.id,
            }
        )

        unread_article = await self.service.article_repo.create(
            {
                "feed_id": feed.id,
                "guid": "unread-article-guid",
                "title": "Unread article",
                "summary": "A short unread article",
                "url": "https://example.org/unread",
                "author": "Author One",
                "content": "Unread content",
                "content_hash": "hash-unread",
                "published_at": datetime.now(UTC),
            }
        )
        saved_article = await self.service.article_repo.create(
            {
                "feed_id": feed.id,
                "guid": "saved-article-guid",
                "title": "Saved article",
                "summary": "A short saved article",
                "url": "https://example.org/saved",
                "author": "Author Two",
                "content": "Saved content",
                "content_hash": "hash-saved",
                "published_at": datetime.now(UTC),
            }
        )

        await self.service.article_status_repo.create(
            {
                "article_id": saved_article.id,
                "user_id": user.id,
                "is_read": False,
                "is_starred": True,
            }
        )

        q = FeverQuery.model_validate(
            {
                "api": True,
                "items": True,
                "unread_item_ids": True,
                "saved_item_ids": True,
            }
        )
        f = FeverForm(api_key=user.fever_key)

        response = await self.service.handle_request(q, f)

        assert response.auth == 1
        assert response.items is not None
        assert response.total_items == 2
        assert response.last_refreshed_on_time == int(feed.last_fetched_at.timestamp())

        item_ids = {item.id for item in response.items}
        assert item_ids == {unread_article.id.int, saved_article.id.int}

        unread_ids = {int(value) for value in response.unread_item_ids.split(",")}  # type: ignore[arg-type]
        assert unread_ids == {unread_article.id.int, saved_article.id.int}

        saved_ids = {int(value) for value in response.saved_item_ids.split(",")}  # type: ignore[arg-type]
        assert saved_ids == {saved_article.id.int}

    async def test_handle_request_returns_feeds_and_feed_groups(self) -> None:
        user = await UserFactory.create()
        user = await self.service.user_repo.get(user.id)

        feed_a = await FeedFactory.create(
            url="https://example.org/a",
            title="Feed A",
            site_url="https://example.org/a",
        )
        feed_b = await FeedFactory.create(
            url="https://example.org/b",
            title="Feed B",
            site_url="https://example.org/b",
        )
        folder = await self.service.folder_repo.create({"user_id": user.id, "name": "Tech"})

        await self.service.feed_subscription_repo.create({"user_id": user.id, "feed_id": feed_a.id})
        await self.service.feed_subscription_repo.create(
            {"user_id": user.id, "feed_id": feed_b.id, "folder_id": folder.id}
        )

        q = FeverQuery.model_validate({"api": True, "feeds": True, "feeds_groups": True})
        f = FeverForm(api_key=user.fever_key)

        response = await self.service.handle_request(q, f)

        assert response.auth == 1
        assert len(response.feeds) == 2
        assert {feed.id for feed in response.feeds} == {feed_a.id.int, feed_b.id.int}
        assert response.feeds_groups is not None
        assert any(group.group_id == 0 and str(feed_a.id.int) in group.feed_ids for group in response.feeds_groups)
        assert any(
            group.group_id == folder.id.int and str(feed_b.id.int) in group.feed_ids for group in response.feeds_groups
        )

    async def test_handle_request_returns_groups_for_user_folders(self) -> None:
        user = await UserFactory.create()
        user = await self.service.user_repo.get(user.id)

        feed = await FeedFactory.create(
            url="https://example.org/grouped",
            title="Grouped Feed",
            site_url="https://example.org/grouped",
        )
        folder = await self.service.folder_repo.create({"user_id": user.id, "name": "News"})

        await self.service.feed_subscription_repo.create(
            {"user_id": user.id, "feed_id": feed.id, "folder_id": folder.id}
        )

        q = FeverQuery.model_validate({"api": True, "groups": True})
        f = FeverForm(api_key=user.fever_key)

        response = await self.service.handle_request(q, f)

        assert response.auth == 1
        assert response.groups is not None
        assert {group.title for group in response.groups} == {"Uncategorised", "News"}
        assert any(group.id == folder.id.int and group.title == "News" for group in response.groups)
        assert response.feeds_groups is not None
        assert any(
            group.group_id == folder.id.int and str(feed.id.int) in group.feed_ids for group in response.feeds_groups
        )

    async def test_handle_request_login_returns_auth_and_generates_fever_key(
        self,
    ) -> None:
        user = await UserFactory.create(fever_key=None)
        q = FeverQuery.model_validate({"action": "login"})
        f = FeverForm(username=user.email, password="password")

        response = await self.service.handle_request(q, f)

        assert response.auth == 1

        updated_user = await self.service.user_repo.get(user.id)
        assert updated_user.fever_key is not None

    async def test_handle_request_login_with_invalid_password_returns_auth_zero(
        self,
    ) -> None:
        user = await UserFactory.create(fever_key=None)
        q = FeverQuery.model_validate({"action": "login"})
        f = FeverForm(username=user.email, password="wrong-password")

        response = await self.service.handle_request(q, f)

        assert response.auth == 0

    async def test_handle_request_with_ids_filters_items(self) -> None:
        user = await UserFactory.create()
        user = await self.service.user_repo.get(user.id)

        feed = await FeedFactory.create(
            url="https://example.org/filter",
            title="Filter Feed",
            site_url="https://example.org/filter",
        )

        await self.service.feed_subscription_repo.create({"user_id": user.id, "feed_id": feed.id})

        article_one = await self.service.article_repo.create(
            {
                "feed_id": feed.id,
                "guid": "filter-one",
                "title": "First article",
                "summary": "First summary",
                "url": "https://example.org/one",
                "author": "Author One",
                "content": "Content One",
                "content_hash": "hash-one",
                "published_at": datetime.now(UTC),
            }
        )
        await self.service.article_repo.create(
            {
                "feed_id": feed.id,
                "guid": "filter-two",
                "title": "Second article",
                "summary": "Second summary",
                "url": "https://example.org/two",
                "author": "Author Two",
                "content": "Content Two",
                "content_hash": "hash-two",
                "published_at": datetime.now(UTC),
            }
        )

        q = FeverQuery.model_validate(
            {
                "api": True,
                "items": True,
                "with_ids": str(article_one.id.int),
            }
        )
        f = FeverForm(api_key=user.fever_key)

        response = await self.service.handle_request(q, f)

        assert response.auth == 1
        assert response.items is not None
        assert len(response.items) == 1
        assert response.items[0].id == article_one.id.int

    async def test_handle_request_with_invalid_api_key_returns_auth_zero(self) -> None:
        q = FeverQuery.model_validate({"api": True, "items": True})
        f = FeverForm(api_key="invalid-key")

        response = await self.service.handle_request(q, f)

        assert response.auth == 0
        assert response.items is None
        assert response.total_items is None
