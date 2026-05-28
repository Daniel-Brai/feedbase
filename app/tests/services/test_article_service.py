from uuid import uuid7

import pytest

from filters import ArticleFilter
from lib.ext.fastapi import ServiceError
from lib.pagination import CursorParams
from lib.testing.services import TestServiceIntegrationCase
from schemas import ArticleStatusUpdate
from services.article import ArticleService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import ArticleFactory, ArticleStatusFactory, FeedFactory, FeedSubscriptionFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestArticleService(TestServiceIntegrationCase):

    service_class = ArticleService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_update_article_status_creates_status_if_missing(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        message, status_out, metadata = await self.service.update_article_status(
            user.id,
            article.id,
            ArticleStatusUpdate.model_validate({"is_read": True}),
        )

        assert message == "Article status updated successfully"
        assert metadata is None
        assert status_out.is_read is True
        assert status_out.is_starred is False
        assert status_out.is_bookmarked is False
        assert status_out.read_at is not None

        persisted_status = (
            await self.service.article_status_repo.query()
            .filter_by(article_id=article.id, user_id=user.id)
            .one_or_none()
        )
        assert persisted_status is not None
        assert persisted_status.is_read is True
        assert persisted_status.read_at is not None

    async def test_update_article_status_updates_existing_status(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)
        existing_status = await ArticleStatusFactory.create(
            user=user,
            article=article,
            is_read=False,
            is_starred=False,
            is_bookmarked=False,
        )

        message, status_out, metadata = await self.service.update_article_status(
            user.id,
            article.id,
            ArticleStatusUpdate.model_validate(
                {
                    "is_read": True,
                    "is_starred": True,
                }
            ),
        )

        assert message == "Article status updated successfully"
        assert metadata is None
        assert status_out.is_read is True
        assert status_out.is_starred is True
        assert status_out.read_at is not None

        updated_status = await self.service.article_status_repo.query().filter_by(id=existing_status.id).one_or_none()
        assert updated_status is not None
        assert updated_status.is_read is True
        assert updated_status.is_starred is True

    async def test_list_articles_returns_results_with_feed_title_and_status(
        self,
    ) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article_one = await ArticleFactory.create(feed=feed)
        article_two = await ArticleFactory.create(feed=feed)

        await FeedSubscriptionFactory.create(user=user, feed=feed)
        await ArticleStatusFactory.create(user=user, article=article_one, is_read=False)

        message, articles, metadata = await self.service.list_articles(
            user.id,
            CursorParams(),
            ArticleFilter(statuses=None),
        )

        assert message == "Articles retrieved successfully"
        assert metadata.total == 2
        assert len(articles) == 2
        assert all(article.feed_title == feed.title for article in articles)

        article_map = {article.id: article for article in articles}
        assert article_map[article_one.id].status is not None
        assert article_map[article_one.id].status.is_read is False
        assert article_map[article_two.id].status is None

    async def test_list_articles_filters_unread_articles(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article_one = await ArticleFactory.create(feed=feed)
        article_two = await ArticleFactory.create(feed=feed)

        await FeedSubscriptionFactory.create(user=user, feed=feed)
        await ArticleStatusFactory.create(user=user, article=article_one, is_read=True)
        await ArticleStatusFactory.create(user=user, article=article_two, is_read=False)

        filter_params = ArticleFilter.model_validate({"statuses": {"is_read": False}})

        message, articles, metadata = await self.service.list_articles(
            user.id,
            CursorParams(),
            filter_params,
        )

        assert message == "Articles retrieved successfully"
        assert metadata.total == 1
        assert len(articles) == 1
        assert articles[0].id == article_two.id

    async def test_get_article_returns_article_with_status_and_feed_title(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article = await ArticleFactory.create(feed=feed)

        await FeedSubscriptionFactory.create(user=user, feed=feed)
        await ArticleStatusFactory.create(user=user, article=article, is_read=True, is_starred=True)

        message, article_out, metadata = await self.service.get_article(user.id, article.id)

        assert message == "Article retrieved successfully"
        assert metadata is None
        assert article_out.id == article.id
        assert article_out.feed_title == feed.title
        assert article_out.status is not None
        assert article_out.status.is_read is True
        assert article_out.status.is_starred is True

    async def test_get_article_raises_not_found_if_missing(self) -> None:
        user = await UserFactory.create()
        missing_id = uuid7()

        with pytest.raises(ServiceError) as exc_info:
            await self.service.get_article(user.id, missing_id)

        assert exc_info.value.status_code == 404
        assert "Article not found" in str(exc_info.value)

    async def test_get_article_stats_returns_counts(self) -> None:
        user = await UserFactory.create()
        feed = await FeedFactory.create()
        article_one = await ArticleFactory.create(feed=feed)
        article_two = await ArticleFactory.create(feed=feed)

        await FeedSubscriptionFactory.create(user=user, feed=feed)
        await ArticleStatusFactory.create(user=user, article=article_one, is_read=True, is_starred=True)
        await ArticleStatusFactory.create(user=user, article=article_two, is_read=False, is_bookmarked=True)

        message, stats_out, metadata = await self.service.get_article_stats(user.id)

        assert message == "Article stats retrieved successfully"
        assert metadata is None
        assert stats_out.total == 2
        assert stats_out.unread == 1
        assert stats_out.starred == 1
        assert stats_out.bookmarked == 1
        assert stats_out.today == 2
