from uuid import uuid7

import pytest

from enums import ArticleAnnotationKind
from lib.ext.fastapi import ServiceError
from lib.pagination import CursorParams
from lib.testing.services import TestServiceIntegrationCase
from schemas import ArticleAnnotationCreate, ArticleAnnotationUpdate
from services.article_annotation import ArticleAnnotationService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import ArticleAnnotationFactory, ArticleFactory, FeedFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestArticleAnnotationService(TestServiceIntegrationCase):

    service_class = ArticleAnnotationService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_list_annotations_returns_annotations_for_article(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        first_annotation = await ArticleAnnotationFactory.create(user=user, article=article, body="First note")
        second_annotation = await ArticleAnnotationFactory.create(user=user, article=article, body="Second note")

        message, annotations, metadata = await self.service.list_annotations(
            user.id,
            article.id,
            CursorParams(),
        )

        assert message == "Annotations retrieved successfully"
        assert metadata.total == 2
        assert len(annotations) == 2
        assert annotations[0].id == second_annotation.id
        assert annotations[0].body == second_annotation.body
        assert annotations[1].id == first_annotation.id
        assert annotations[1].body == first_annotation.body

    async def test_get_article_annotation_count_returns_correct_count(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        await ArticleAnnotationFactory.create(user=user, article=article)
        await ArticleAnnotationFactory.create(user=user, article=article)

        message, count, metadata = await self.service.get_article_annotation_count(user.id, article.id)

        assert message == "Annotation count retrieved successfully"
        assert count == 2
        assert metadata is None

    async def test_add_article_annotation_creates_annotation(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        data = ArticleAnnotationCreate.model_validate(
            {
                "article_id": article.id,
                "kind": ArticleAnnotationKind.NOTES,
                "body": "A test annotation",
            }
        )

        message, annotation_out, metadata = await self.service.add_article_annotation(user.id, data)

        assert message == "Annotation added successfully"
        assert metadata is None
        assert annotation_out.article_id == article.id
        assert annotation_out.body == "A test annotation"

        persisted_annotation = (
            await self.service.article_annotation_repo.query().filter_by(id=annotation_out.id).one_or_none()
        )
        assert persisted_annotation is not None
        assert persisted_annotation.user_id == user.id
        assert persisted_annotation.article_id == article.id
        assert persisted_annotation.body == "A test annotation"

    async def test_add_article_annotation_raises_not_found_if_article_missing(
        self,
    ) -> None:
        user = await UserFactory.create()
        missing_article_id = uuid7()

        data = ArticleAnnotationCreate.model_validate(
            {
                "article_id": missing_article_id,
                "kind": ArticleAnnotationKind.NOTES,
                "body": "A missing article annotation",
            }
        )

        with pytest.raises(ServiceError) as exc_info:
            await self.service.add_article_annotation(user.id, data)

        assert exc_info.value.status_code == 404
        assert "Article not found" in str(exc_info.value)

    async def test_update_article_annotation_updates_existing_annotation(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)
        annotation = await ArticleAnnotationFactory.create(
            user=user,
            article=article,
            body="Original text",
            color="#ff0000",
        )

        data = ArticleAnnotationUpdate.model_validate(
            {
                "body": "Updated text",
                "color": "#0000ff",
            }
        )

        message, updated_annotation, metadata = await self.service.update_article_annotation(
            user.id,
            annotation.id,
            data,
        )

        assert message == "Annotation updated successfully"
        assert metadata is None
        assert updated_annotation.id == annotation.id
        assert updated_annotation.body == "Updated text"

        persisted_annotation = (
            await self.service.article_annotation_repo.query().filter_by(id=annotation.id).one_or_none()
        )
        assert persisted_annotation is not None
        assert persisted_annotation.body == "Updated text"
        assert persisted_annotation.color == "#0000ff"

    async def test_update_article_annotation_raises_not_found_if_missing(self) -> None:
        user = await UserFactory.create()
        missing_annotation_id = uuid7()

        data = ArticleAnnotationUpdate.model_validate({"body": "Should not save"})

        with pytest.raises(ServiceError) as exc_info:
            await self.service.update_article_annotation(user.id, missing_annotation_id, data)

        assert exc_info.value.status_code == 404
        assert "Annotation not found" in str(exc_info.value)

    async def test_delete_article_annotation_removes_annotation(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)
        annotation = await ArticleAnnotationFactory.create(user=user, article=article)

        message = await self.service.delete_article_annotation(user.id, annotation.id)

        assert message == "Annotation deleted successfully"

        deleted_annotation = (
            await self.service.article_annotation_repo.query().filter_by(id=annotation.id).one_or_none()
        )
        assert deleted_annotation is None

    async def test_delete_article_annotation_raises_not_found_if_missing(self) -> None:
        user = await UserFactory.create()
        missing_annotation_id = uuid7()

        with pytest.raises(ServiceError) as exc_info:
            await self.service.delete_article_annotation(user.id, missing_annotation_id)

        assert exc_info.value.status_code == 404
        assert "Annotation not found" in str(exc_info.value)
