import asyncio
from pathlib import Path

import httpx

from enums import FeedFetchStatus
from services.feed_parser import FeedParserService


async def _benchmark_parse_response(service: FeedParserService, url: str, response: httpx.Response) -> object:
    return await service.parse_response(url, response)


def test_feed_parser_parse_response_benchmark(benchmark, test_support_data_dir: Path) -> None:

    url = "https://example.org/feed.xml"
    xml_path = test_support_data_dir / "feeds" / "feed_fetcher_feed.xml"
    feed_content = xml_path.read_bytes()

    loop = asyncio.new_event_loop()

    async_client = httpx.AsyncClient()
    service = FeedParserService(async_client)
    response = httpx.Response(
        200,
        content=feed_content,
        headers={
            "ETag": 'W/"abc"',
            "Last-Modified": "Wed, 01 Jan 2025 00:00:00 GMT",
        },
        request=httpx.Request("GET", url),
    )

    def run() -> object:
        return loop.run_until_complete(_benchmark_parse_response(service, url, response))

    # Here the parser is warmed up twice so the benchmark measures steady state performance
    run()
    run()

    result = benchmark.pedantic(
        run,
        rounds=8,
        iterations=3,
        warmup_rounds=2,
    )

    assert result.status == FeedFetchStatus.OK
    assert result.feed_meta is not None
    assert result.feed_meta.title == "Fetcher Test Feed"
    assert len(result.entries) == 2

    loop.run_until_complete(async_client.aclose())
    loop.close()
