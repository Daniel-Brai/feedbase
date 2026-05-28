import asyncio
from urllib.parse import urlparse

import feedparser_rs as feedparser
import httpx
from bs4 import BeautifulSoup
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from constants import FEED_FETCHER_HEADERS, FEED_TYPES, FEED_TYPES_RELEVANCE
from lib.ext.fastapi import IORunnableService, ServiceError
from schemas import DiscoveredFeed, FeedDiscoverCreate, FeedDiscoverOut

from .feed_enricher import FeedEnricherService


class FeedDiscoveryService(IORunnableService):
    """
    Service for managing feed discovery
    """

    def __init__(self, http_client: AsyncClient, db: AsyncSession) -> None:
        super().__init__(db)

        self.feed_enricher_svc = FeedEnricherService(http_client)

    def _looks_like_feed_url(self, url: str) -> bool:
        url_lower = url.lower()
        return url_lower.endswith((".rss", ".atom", ".xml", ".json")) or url_lower.endswith("/feed")

    def _guess_feed_mime(self, response: httpx.Response, url: str) -> str:
        content_type = response.headers.get("content-type", "").lower()
        for mime in FEED_TYPES:
            if mime in content_type:
                return mime

        url_lower = url.lower()
        if url_lower.endswith(".atom"):
            return "application/atom+xml"
        if url_lower.endswith(".json"):
            return "application/json"
        return "application/rss+xml"

    def _response_is_feed(self, response: httpx.Response) -> bool:
        content_type = response.headers.get("content-type", "").lower()
        if any(mime in content_type for mime in FEED_TYPES):
            return True

        text = response.text.lstrip()
        if text.startswith("<?xml"):
            return True

        return self._looks_like_feed_url(str(response.url)) and "html" not in content_type

    async def _parse_feed_title(self, response: httpx.Response) -> str:
        try:
            parsed = await asyncio.to_thread(feedparser.parse, response.content)
            return str(parsed.feed.title or "")
        except Exception:
            return ""

    async def run(
        self,
        http_client: AsyncClient,
        data: FeedDiscoverCreate,
    ) -> tuple[str, list[FeedDiscoverOut] | None, None]:
        """
        Main entrypoint to discover feeds by passing a URL before the feed is added as a subscription.

        Args:
            data (FeedDiscoverCreate): The data required to discover a feed, including the URL to fetch.

        Returns:
            (str, list[FeedDiscoverOut] | None, None): A tuple containing a message, a list of discovered feeds (if any), and None for metadata (for consistency with other service methods).
        """

        try:
            response = await http_client.get(str(data.url), headers=FEED_FETCHER_HEADERS)
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Error fetching URL {data.url}: {e}")
            raise ServiceError(
                "Failed to fetch the provided URL. Please ensure the URL is correct and the server is reachable."
            ) from e

        try:
            found: list[DiscoveredFeed] = []

            if self._response_is_feed(response):
                mime = self._guess_feed_mime(response, str(data.url))
                title = await self._parse_feed_title(response)
                found.append(
                    DiscoveredFeed(
                        url=str(data.url),
                        title=title,
                        mime=mime,
                        priority=FEED_TYPES_RELEVANCE.get(mime, 2),
                    )
                )
            else:
                parser = "html.parser"
                soup = BeautifulSoup(response.text, parser)
                base = urlparse(str(data.url))

                for link in soup.find_all("link", rel="alternate"):
                    mime_value = link.get("type", "")
                    if isinstance(mime_value, list):
                        mime_value = mime_value[0] if mime_value else ""

                    mime = mime_value.lower() if mime_value else ""

                    href_value = link.get("href", "")
                    if isinstance(href_value, list):
                        href_value = href_value[0] if href_value else ""
                    href = str(href_value).strip()

                    if not href or mime not in FEED_TYPES:
                        continue

                    if href.startswith("/"):
                        href = f"{base.scheme}://{base.netloc}{href}"
                    elif not href.startswith("http"):
                        continue

                    title_value = link.get("title", "")
                    if isinstance(title_value, list):
                        title_value = title_value[0] if title_value else ""

                    title = str(title_value).strip() if title_value else ""

                    found.append(
                        DiscoveredFeed(
                            url=href,
                            title=title,
                            mime=mime,
                            priority=FEED_TYPES_RELEVANCE.get(mime, 2),
                        )
                    )

            groups: dict[str, list[DiscoveredFeed]] = {}
            for f in found:
                path = urlparse(f.url).path.lower()
                for suffix in (".rss", ".atom", ".xml", ".json"):
                    if path.endswith(suffix):
                        path = path[: -len(suffix)]

                groups.setdefault(path, []).append(f)

            deduped_feeds: list[DiscoveredFeed] = []
            for group in groups.values():
                best = sorted(group, key=lambda x: x.priority)[0]
                deduped_feeds.append(best)

            deduped_feeds = await self.feed_enricher_svc.run(deduped_feeds)

            deduped_feeds.sort(key=lambda x: (x.priority, x.title.lower()))

            return (
                "Feeds discovered successfully",
                [FeedDiscoverOut(value=f.url, text=f.title or f.url) for f in deduped_feeds],
                None,
            )
        except Exception as e:
            self.logger.error(f"Error parsing URL {data.url}: {e}")
            raise ServiceError(
                "Failed to parse the provided URL and discover feeds. Please ensure the URL points to a valid webpage."
            ) from e
