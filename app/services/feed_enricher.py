import asyncio

import feedparser_rs as feedparser
import httpx

from constants import FEED_FETCHER_HEADERS
from lib.ext.fastapi import StandaloneRunnableService
from schemas import DiscoveredFeed, FeedFetchHints


class FeedEnricherService(StandaloneRunnableService):
    """
    Service for enriching feed metadata
    """

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        super().__init__()

        self._client = http_client

    async def run(self, feeds: list[DiscoveredFeed]) -> list[DiscoveredFeed]:
        """
        Enriches feed metadata with titles by fetching the feed URL and parsing it if the title is missing.

        This is used to improve the display of discovered feeds that may not have a title in the link tag.
        """

        self.logger.info(f"FeedEnricherService: enriching {len(feeds)} feeds")

        async def fetch_title(f: DiscoveredFeed) -> DiscoveredFeed:
            if f.title:
                return f
            try:
                r = await self._http_get(f.url, FeedFetchHints())
                r.raise_for_status()

                parsed = await asyncio.to_thread(feedparser.parse, r.content)
                f.title = parsed.feed.title or ""
            except Exception as exc:
                self.logger.debug(f"FeedEnricherService: failed to enrich title for {f.url}: {exc}")

            return f

        results = await asyncio.gather(*[fetch_title(f) for f in feeds])
        self.logger.info(f"FeedEnricherService: enriched {len(results)} feeds")

        return results

    async def _http_get(self, url: str, hints: FeedFetchHints) -> httpx.Response:
        headers = {**FEED_FETCHER_HEADERS}
        if hints.etag:
            headers["If-None-Match"] = hints.etag

        if hints.last_modified:
            headers["If-Modified-Since"] = hints.last_modified

        return await self._client.get(url, headers=headers)
