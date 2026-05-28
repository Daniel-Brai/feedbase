from pathlib import Path

import httpx
import pytest

from enums import FeedFetchStatus
from services.feed_parser import FeedParserService


@pytest.mark.asyncio
class TestFeedParserService:

    async def test_parse_response_returns_parsed_feed_result(self, test_support_data_dir: Path) -> None:
        url = "https://example.org/feed.xml"
        xml_path = test_support_data_dir / "feeds" / "feed_fetcher_feed.xml"
        feed_content = xml_path.read_bytes()

        async with httpx.AsyncClient() as client:
            service = FeedParserService(client)
            response = httpx.Response(
                200,
                content=feed_content,
                headers={
                    "ETag": 'W/"abc"',
                    "Last-Modified": "Wed, 01 Jan 2025 00:00:00 GMT",
                },
                request=httpx.Request("GET", url),
            )

            result = await service.parse_response(url, response)

        assert result.status == FeedFetchStatus.OK
        assert result.feed_meta is not None
        assert result.feed_meta.title == "Fetcher Test Feed"
        assert result.feed_meta.site_url == "https://example.org/"
        assert result.etag == 'W/"abc"'
        assert result.last_modified == "Wed, 01 Jan 2025 00:00:00 GMT"
        assert len(result.entries) == 2
        assert {entry.guid for entry in result.entries} == {
            "article-one",
            "article-two",
        }
        assert {entry.title for entry in result.entries} == {
            "Article One",
            "Article Two",
        }

    async def test_parse_response_returns_error_on_invalid_feed(self) -> None:
        url = "https://example.org/invalid.xml"

        async with httpx.AsyncClient() as client:
            service = FeedParserService(client)
            response = httpx.Response(
                200,
                content=b"not xml",
                request=httpx.Request("GET", url),
            )

            result = await service.parse_response(url, response)

        assert result.status == FeedFetchStatus.ERROR
        assert result.error_message is not None
        assert result.feed_meta is None
