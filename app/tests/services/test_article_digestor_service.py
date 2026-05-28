from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from lib.mailer.exceptions import MailerNotConfiguredError
from lib.testing.services import TestIORunnableServiceIntegrationCase
from services.article_digestor import ArticleDigestService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import ArticleFactory, FeedFactory, FeedSubscriptionFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestArticleDigestService(TestIORunnableServiceIntegrationCase):

    service_class = ArticleDigestService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_no_mailer_configured_aborts_digest_job(self) -> None:
        now = datetime.now(UTC)
        user = await UserFactory.create(
            preferences={
                "digest_frequency": "daily",
                "digest_hour": now.hour,
            }
        )

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(user=user, feed=feed)
        await ArticleFactory.create(feed=feed, published_at=now - timedelta(hours=2))

        with patch("lib.mailer.get_mailer", side_effect=MailerNotConfiguredError("No mailer")) as mock_get_mailer:
            await self.service.run()

        mock_get_mailer.assert_called_once()

        user = await self.service.user_repo.get(user.id)
        assert user.preferences.get("last_digest_sent") is None

    async def test_skip_digest_when_hour_has_not_arrived(self) -> None:
        now = datetime.now(UTC)
        next_hour = (now.hour + 1) % 24
        user = await UserFactory.create(
            preferences={
                "digest_frequency": "daily",
                "digest_hour": next_hour,
            }
        )

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(user=user, feed=feed)
        await ArticleFactory.create(feed=feed, published_at=now - timedelta(hours=1))

        mailer = AsyncMock()
        mailer.send_template = AsyncMock()

        with patch("lib.mailer.get_mailer", return_value=mailer):
            await self.service.run()

        mailer.send_template.assert_not_awaited()

        user = await self.service.user_repo.get(user.id)
        assert user.preferences.get("last_digest_sent") is None

    async def test_sends_daily_digest_for_unread_articles(self) -> None:
        now = datetime.now(UTC)
        user = await UserFactory.create(
            preferences={
                "digest_frequency": "daily",
                "digest_hour": now.hour,
            }
        )

        feed = await FeedFactory.create(
            title="Daily News",
            url="https://example.org/daily.xml",
        )
        await FeedSubscriptionFactory.create(user=user, feed=feed)
        article = await ArticleFactory.create(
            feed=feed,
            title="Daily Article",
            summary="A short summary.",
            url="https://example.org/daily/article",
            published_at=now - timedelta(hours=2),
        )

        mailer = AsyncMock()
        mailer.send_template = AsyncMock()

        with patch("lib.mailer.get_mailer", return_value=mailer):
            await self.service.run()

        mailer.send_template.assert_awaited_once()
        sent_kwargs = mailer.send_template.await_args.kwargs

        assert sent_kwargs["to"] == user.email
        assert "daily" in sent_kwargs["subject"].lower()
        assert sent_kwargs["template"] == "email_digest.mjml.html"
        assert sent_kwargs["context"]["frequency"] == "daily"
        assert sent_kwargs["context"]["feeds"][0]["feed_title"] == feed.title
        assert sent_kwargs["context"]["feeds"][0]["articles"][0]["title"] == article.title
        assert sent_kwargs["context"]["feeds"][0]["articles"][0]["url"] == article.url
        assert sent_kwargs["context"]["feeds"][0]["articles"][0]["summary"] == article.summary

        user = await self.service.user_repo.get(user.id)

        assert user is not None

        last_sent = user.preferences.get("last_digest_sent")
        assert last_sent is not None
        assert datetime.fromisoformat(last_sent) <= datetime.now(UTC)

    async def test_does_not_send_digest_when_no_unread_articles(self) -> None:
        now = datetime.now(UTC)
        user = await UserFactory.create(
            preferences={
                "digest_frequency": "daily",
                "digest_hour": now.hour,
            }
        )

        feed = await FeedFactory.create()
        await FeedSubscriptionFactory.create(user=user, feed=feed)

        mailer = AsyncMock()
        mailer.send_template = AsyncMock()

        with patch("lib.mailer.get_mailer", return_value=mailer):
            await self.service.run()

        mailer.send_template.assert_not_awaited()

        user = await self.service.user_repo.get(user.id)
        assert user.preferences.get("last_digest_sent") is None
