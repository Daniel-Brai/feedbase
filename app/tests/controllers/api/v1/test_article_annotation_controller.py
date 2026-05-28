import pytest

from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from lib.testing import TestControllerIntegrationCase
from models import ArticleAnnotation
from services import ArticleAnnotationService
from settings import settings
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import ArticleAnnotationFactory, ArticleFactory, FeedFactory
from tests.utils import create_verified_user, get_auth_token, mount_auth_routes

configure_auth()

from controllers.api.v1 import ArticleAnnotationController


@pytest.mark.integration
@pytest.mark.asyncio
class TestArticleAnnotationController(TestControllerIntegrationCase):

    controller_class = ArticleAnnotationController
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def asyncSetUp(self) -> None:
        configure_controllers()

        await super().asyncSetUp()

        from dependencies.article import get_article_annotation_service

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

    async def test_add_annotation_creates_annotation(self) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        response = await self.client.post(
            f"{settings.API_V1_STR}/annotations",
            json={
                "article_id": str(article.id),
                "kind": "note",
                "body": "This is a test annotation.",
            },
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Annotation added successfully"
        assert payload["data"]["article_id"] == str(article.id)
        assert payload["data"]["body"] == "This is a test annotation."
        assert payload["data"]["kind"] == "note"
        assert payload["data"]["id"] is not None

    async def test_update_annotation_updates_annotation(self) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)
        annotation = await ArticleAnnotationFactory.create(
            user=self.user,
            article=article,
            body="Initial body",
        )

        response = await self.client.patch(
            f"{settings.API_V1_STR}/annotations/{annotation.id}",
            json={
                "body": "Updated body",
                "color": "#ff0000",
            },
        )

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Annotation updated successfully"
        assert payload["data"]["body"] == "Updated body"
        assert payload["data"]["color"] == "#ff0000"

    async def test_delete_annotation_removes_annotation(self) -> None:
        await self.authenticate_user()

        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)
        annotation = await ArticleAnnotationFactory.create(user=self.user, article=article)

        response = await self.client.delete(f"{settings.API_V1_STR}/annotations/{annotation.id}")

        self.assert_ok(response)
        payload = response.json()

        assert payload["message"] == "Annotation deleted successfully"

        deleted = await self.db.get(ArticleAnnotation, annotation.id)
        assert deleted is None

    async def test_add_annotation_returns_401_for_unauthenticated_user(self) -> None:
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        response = await self.client.post(
            f"{settings.API_V1_STR}/annotations",
            json={
                "article_id": str(article.id),
                "kind": "note",
                "body": "Unauthorized",
            },
        )

        self.assert_unauthorized(response)
