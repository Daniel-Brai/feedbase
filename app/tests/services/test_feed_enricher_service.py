from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from schemas import DiscoveredFeed
from services.feed_enricher import FeedEnricherService


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedEnricherService:

    async def test_run_enriches_feed_title_when_missing(self, test_support_data_dir: Path) -> None:
        xml_path = test_support_data_dir / "feeds" / "enriched_feed.xml"
        content = xml_path.read_bytes()

        async with httpx.AsyncClient() as client:
            service = FeedEnricherService(client)
            response = httpx.Response(
                200,
                content=content,
                request=httpx.Request("GET", "https://example.org/feed.xml"),
            )
            service._http_get = AsyncMock(return_value=response)

            feed = DiscoveredFeed(
                url="https://example.org/feed.xml",
                title="",
                mime="application/rss+xml",
                priority=0,
            )

            enriched = await service.run([feed])

        assert len(enriched) == 1
        assert enriched[0].url == "https://example.org/feed.xml"
        assert enriched[0].mime == "application/rss+xml"
        assert enriched[0].title == "Enriched Feed Title"
        service._http_get.assert_awaited_once()

    async def test_run_keeps_existing_title_and_skips_fetch(self) -> None:
        async with httpx.AsyncClient() as client:
            service = FeedEnricherService(client)
            service._http_get = AsyncMock()

            feed = DiscoveredFeed(
                url="https://example.org/feed.xml",
                title="Already Known",
                mime="application/rss+xml",
                priority=0,
            )

            enriched = await service.run([feed])

        assert len(enriched) == 1
        assert enriched[0].title == "Already Known"
        service._http_get.assert_not_awaited()
