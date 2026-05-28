from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from lib.ext.fastapi import ServiceError
from schemas import FeedDiscoverCreate, FeedDiscoverOut
from services.feed_discovery import FeedDiscoveryService


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedDiscoveryService:

    async def test_run_discovers_feed_from_rss_xml_response(self, test_support_data_dir: Path) -> None:
        url = "https://example.org/feed.xml"
        rss_path = test_support_data_dir / "feeds" / "discovery_feed.xml"
        rss_content = rss_path.read_bytes()

        http_client = Mock()
        http_client.get = AsyncMock(
            return_value=httpx.Response(
                200,
                content=rss_content,
                headers={"content-type": "application/rss+xml"},
                request=httpx.Request("GET", url),
            )
        )

        service = FeedDiscoveryService(http_client, Mock())
        data = FeedDiscoverCreate.model_validate({"url": url})

        message, discovered, metadata = await service.run(http_client, data)

        assert message == "Feeds discovered successfully"
        assert metadata is None
        assert discovered == [
            FeedDiscoverOut(value=url, text="Example Feed"),
        ]

    async def test_run_discovers_feed_links_from_html_page(self, test_support_data_dir: Path) -> None:
        url = "https://example.org/page"
        html_path = test_support_data_dir / "feeds" / "discovery_page.html"
        html_content = html_path.read_bytes()

        http_client = Mock()
        http_client.get = AsyncMock(
            return_value=httpx.Response(
                200,
                content=html_content,
                headers={"content-type": "text/html"},
                request=httpx.Request("GET", url),
            )
        )

        service = FeedDiscoveryService(http_client, Mock())
        data = FeedDiscoverCreate.model_validate({"url": url})

        message, discovered, metadata = await service.run(http_client, data)

        assert message == "Feeds discovered successfully"
        assert metadata is None
        assert discovered == [
            FeedDiscoverOut(value="https://example.org/feed1.xml", text="Feed One"),
            FeedDiscoverOut(value="https://example.org/other_feed.xml", text="Other Feed"),
        ]

    async def test_run_raises_service_error_when_fetch_fails(self) -> None:
        url = "https://example.org/broken"

        http_client = Mock()
        http_client.get = AsyncMock(side_effect=Exception("connection error"))

        service = FeedDiscoveryService(http_client, Mock())
        data = FeedDiscoverCreate.model_validate({"url": url})

        with pytest.raises(ServiceError) as exc_info:
            await service.run(http_client, data)

        assert "Failed to fetch the provided URL" in str(exc_info.value)
