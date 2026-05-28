from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from lib.testing.services import TestServiceIntegrationCase
from services.feed_fetcher import FeedFetcherService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedFetcherService(TestServiceIntegrationCase):

    service_class = FeedFetcherService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_fetches_and_parses_live_atom_feed(self) -> None:
        feed = await self.service.feed_repo.create(
            {
                "url": "https://matklad.github.io/feed.xml",
                "title": None,
                "description": None,
                "site_url": None,
            }
        )

        new_articles, updated_articles = await self.service.run(feed)

        assert new_articles > 0
        assert updated_articles == 0

        refreshed_feed = await self.service.feed_repo.get_by(id=feed.id)

        assert refreshed_feed is not None
        assert refreshed_feed.title == "matklad"
        assert refreshed_feed.site_url == "https://matklad.github.io"
        assert refreshed_feed.last_fetched_at is not None
        assert refreshed_feed.error_count == 0
        assert refreshed_feed.last_error is None

        articles = await self.service.article_repo.get_all_articles_for_feed(feed.id)
        assert len(articles) == new_articles
        assert len(articles) > 0

        first_article = articles[0]
        assert first_article.guid
        assert first_article.url
        assert first_article.title

    async def test_run_creates_articles_from_parsed_feed(self) -> None:
        feed = await self.service.feed_repo.create(
            {
                "url": "https://example.org/feed.xml",
                "title": None,
                "description": None,
                "site_url": None,
            }
        )

        test_support_data_dir = Path(__file__).resolve().parent.parent / "support"
        xml_path = test_support_data_dir / "feeds" / "feed_fetcher_feed.xml"
        feed_content = xml_path.read_bytes()

        self.service._http_get = AsyncMock(
            return_value=httpx.Response(
                200,
                content=feed_content,
                headers={"content-type": "application/rss+xml"},
                request=httpx.Request("GET", feed.url),
            )
        )

        new_articles, updated_articles = await self.service.run(feed)

        assert new_articles == 2
        assert updated_articles == 0

        refreshed_feed = await self.service.feed_repo.get_by(id=feed.id)
        assert refreshed_feed is not None
        assert refreshed_feed.title == "Fetcher Test Feed"
        assert refreshed_feed.last_fetched_at is not None
        assert refreshed_feed.error_count == 0
        assert refreshed_feed.last_error is None

        articles = await self.service.article_repo.get_all_articles_for_feed(feed.id)
        assert len(articles) == 2
        assert {article.guid for article in articles} == {"article-one", "article-two"}

    async def test_run_updates_feed_last_fetched_at_when_not_modified(self) -> None:
        feed = await self.service.feed_repo.create(
            {
                "url": "https://example.org/feed.xml",
                "title": "Existing Feed",
                "description": "Existing description",
                "site_url": "https://example.org",
                "etag": "test-etag",
                "last_modified": "Wed, 01 Jan 2025 00:00:00 GMT",
            }
        )

        self.service._http_get = AsyncMock(
            return_value=httpx.Response(
                304,
                request=httpx.Request("GET", feed.url),
            )
        )

        new_articles, updated_articles = await self.service.run(feed)

        assert new_articles == 0
        assert updated_articles == 0

        refreshed_feed = await self.service.feed_repo.get_by(id=feed.id)
        assert refreshed_feed is not None
        assert refreshed_feed.last_fetched_at is not None

    async def test_run_increments_error_count_on_http_failure(self) -> None:
        feed = await self.service.feed_repo.create(
            {
                "url": "https://example.org/fail.xml",
                "title": "Failing Feed",
                "description": None,
                "site_url": None,
                "error_count": 0,
            }
        )

        self.service._http_get = AsyncMock(
            return_value=httpx.Response(
                500,
                request=httpx.Request("GET", feed.url),
            )
        )

        new_articles, updated_articles = await self.service.run(feed)

        assert new_articles == 0
        assert updated_articles == 0

        refreshed_feed = await self.service.feed_repo.get_by(id=feed.id)
        assert refreshed_feed is not None
        assert refreshed_feed.error_count == 1
        assert refreshed_feed.last_error == "HTTP 500"
