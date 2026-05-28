import pytest

from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from lib.testing import TestControllerIntegrationCase
from services import ArticleAnnotationService, ArticleService
from settings import settings
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import (
    ArticleAnnotationFactory,
    ArticleFactory,
    ArticleStatusFactory,
    FeedFactory,
    FeedSubscriptionFactory,
)
from tests.utils import create_verified_user, get_auth_token, mount_auth_routes

configure_auth()


from controllers.api.v1 import ArticleController


@pytest.mark.integration
@pytest.mark.asyncio
class TestArticleController(TestControllerIntegrationCase):

    controller_class = ArticleController
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def asyncSetUp(self) -> None:

        configure_controllers()

        await super().asyncSetUp()

        from dependencies.article import get_article_annotation_service, get_article_service

        self.override_dependency(
            get_article_service,
            lambda: ArticleService(self.db),
        )
        self.override_dependency(
            get_article_annotation_service,
            lambda: ArticleAnnotationService(self.db),
        )

        mount_auth_routes(self.app)

        self.user = None
        self.auth_cookies = {}

    async def authenticate_user(self) -> None:
        self.user, user_password = await create_verified_user()
        self.auth_cookies = await get_auth_token(self.client, self.user.email, user_password)
        self.client.cookies.update(self.auth_cookies)

    async def test_list_articles_returns_articles_for_the_authenticated_user(
        self,
    ) -> None:

        await self.authenticate_user()

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(
            user=self.user,
            feed=feed,
            title="Subscribed Feed Title",
        )

        article_one = await ArticleFactory.create(feed=feed)

        article_two = await ArticleFactory.create(feed=feed)

        await ArticleStatusFactory.create(user=self.user, article=article_one, is_read=False)

        response = await self.client.get(f"{settings.API_V1_STR}/articles", params={"size": 10})

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Articles retrieved successfully"
        assert payload["metadata"]["total"] == 2
        assert len(payload["data"]) == 2

        article_map = {article["id"]: article for article in payload["data"]}

        assert "feed_title" in article_map[str(article_one.id)]
        assert article_map[str(article_one.id)]["status"] is not None
        assert article_map[str(article_one.id)]["status"]["is_read"] is False
        assert article_map[str(article_two.id)]["status"] is None

    async def test_get_article_returns_article_details_with_status(self) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(
            user=self.user,
            feed=feed,
            title="Subscribed Feed Title",
        )

        article = await ArticleFactory.create(feed=feed)
        await ArticleStatusFactory.create(user=self.user, article=article, is_read=True, is_starred=True)

        response = await self.client.get(f"{settings.API_V1_STR}/articles/{article.id}")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Article retrieved successfully"
        assert payload["data"]["id"] == str(article.id)
        assert "feed_title" in payload["data"]
        assert payload["data"]["status"]["is_read"] is True
        assert payload["data"]["status"]["is_starred"] is True

    async def test_update_article_status_updates_existing_status(self) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(user=self.user, feed=feed)

        article = await ArticleFactory.create(feed=feed)
        await ArticleStatusFactory.create(user=self.user, article=article, is_read=False, is_starred=False)

        response = await self.client.patch(
            f"{settings.API_V1_STR}/articles/{article.id}/status",
            json={"is_read": True, "is_starred": True},
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Article status updated successfully"
        assert payload["data"]["is_read"] is True
        assert payload["data"]["is_starred"] is True

    async def test_get_article_annotations_and_annotation_count(self) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()

        await FeedSubscriptionFactory.create(user=self.user, feed=feed)

        article = await ArticleFactory.create(feed=feed)
        await ArticleAnnotationFactory.create(user=self.user, article=article)
        await ArticleAnnotationFactory.create(user=self.user, article=article)

        other_article = await ArticleFactory.create(feed=feed)
        await ArticleAnnotationFactory.create(user=self.user, article=other_article)

        annotations_response = await self.client.get(
            f"{settings.API_V1_STR}/articles/{article.id}/annotations",
        )

        self.assert_ok(annotations_response)
        annotations_payload = annotations_response.json()

        assert annotations_payload["message"] == "Annotations retrieved successfully"
        assert annotations_payload["metadata"]["total"] == 2
        assert len(annotations_payload["data"]) == 2

        count_response = await self.client.get(
            f"{settings.API_V1_STR}/articles/{article.id}/annotations/count",
        )

        self.assert_ok(count_response)
        count_payload = count_response.json()

        assert count_payload["message"] == "Annotation count retrieved successfully"
        assert count_payload["data"] == 2

    async def test_get_article_stats_returns_counts_for_authenticated_user(
        self,
    ) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(user=self.user, feed=feed)

        article_one = await ArticleFactory.create(feed=feed)
        article_two = await ArticleFactory.create(feed=feed)

        await ArticleStatusFactory.create(user=self.user, article=article_one, is_read=False)
        await ArticleStatusFactory.create(user=self.user, article=article_two, is_read=True, is_starred=True)

        response = await self.client.get(f"{settings.API_V1_STR}/articles/stats")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Article stats retrieved successfully"
        assert payload["data"]["total"] == 2
        assert payload["data"]["unread"] == 1
        assert payload["data"]["starred"] == 1

    async def test_list_articles_returns_401_for_unauthenticated_user(self) -> None:
        response = await self.client.get(f"{settings.API_V1_STR}/articles")

        self.assert_unauthorized(response)
