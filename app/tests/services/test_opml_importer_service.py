from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lib.testing.services import TestServiceIntegrationCase
from services.opml_importer import OPMLImporterService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory, FeedSubscriptionFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestOPMLImporterService(TestServiceIntegrationCase):

    service_class = OPMLImporterService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_run_imports_nested_folder_subscriptions(self) -> None:
        user = await UserFactory.create(name="Importer User", email="importer@example.org")
        test_support_data_dir = Path(__file__).resolve().parent.parent / "support"

        opml_content = (test_support_data_dir / "opml" / "nested_import.opml").read_bytes()

        with patch("services.opml_importer.FetchFeedJob.perform_later", new=Mock()) as mock_job:
            result = await self.service.run(user.id, opml_content)

        assert result.added == 3
        assert result.skipped == 0
        assert result.failed == 0
        assert result.folders_created == 3
        assert result.errors == []
        assert mock_job.called

        root_feed = await self.service.feed_repo.get_by(url="https://example.org/root.xml")
        assert root_feed is not None

        news_feed = await self.service.feed_repo.get_by(url="https://example.org/news.xml")
        assert news_feed is not None
        assert news_feed.site_url == "https://news.example.org"
        assert news_feed.title == "News Feed"

        tech_feed = await self.service.feed_repo.get_by(url="https://example.org/tech.xml")
        assert tech_feed is not None
        assert tech_feed.title == "Tech Feed"

        subscriptions = await self.service.feed_subscription_repo.query().filter_by(user_id=user.id).all()
        assert len(subscriptions) == 3
        assert {sub.feed_id for sub in subscriptions} == {
            root_feed.id,
            news_feed.id,
            tech_feed.id,
        }

    async def test_run_skips_existing_subscriptions(self) -> None:
        user = await UserFactory.create(name="Skip User", email="skip@example.org")
        existing_feed = await FeedFactory.create(url="https://example.org/existing.xml")

        await FeedSubscriptionFactory.create(user=user, feed=existing_feed)
        test_support_data_dir = Path(__file__).resolve().parent.parent / "support"

        opml_content = (test_support_data_dir / "opml" / "existing_subscription.opml").read_bytes()

        result = await self.service.run(user.id, opml_content)

        assert result.added == 0
        assert result.skipped == 1
        assert result.failed == 0
        assert result.folders_created == 0
        assert result.errors == []

        subscriptions = await self.service.feed_subscription_repo.query().filter_by(user_id=user.id).all()
        assert len(subscriptions) == 1

    async def test_run_returns_errors_for_invalid_opml(self) -> None:
        user = await UserFactory.create(name="Bad User", email="bad@example.org")
        test_support_data_dir = Path(__file__).resolve().parent.parent / "support"

        opml_content = (test_support_data_dir / "opml" / "invalid.opml").read_bytes()

        result = await self.service.run(user.id, opml_content)

        assert result.added == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert "Invalid OPML file" in result.errors[0]

    async def test_run_returns_errors_when_body_is_missing(self) -> None:
        user = await UserFactory.create(name="Empty User", email="empty@example.org")
        test_support_data_dir = Path(__file__).resolve().parent.parent / "support"

        opml_content = (test_support_data_dir / "opml" / "no_body.opml").read_bytes()

        result = await self.service.run(user.id, opml_content)

        assert result.added == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert result.errors == ["OPML file has no <body> element"]
