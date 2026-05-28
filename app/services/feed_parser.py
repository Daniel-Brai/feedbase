import asyncio

import feedparser_rs as feedparser
import httpx
import trafilatura
from bs4 import BeautifulSoup

from constants import FEED_FETCHER_HEADERS, FEED_FETCHER_THIN_CONTENT_THRESHOLD
from enums import FeedFetchStatus
from helpers import (
    clean_html_attributes,
    compute_content_hash,
    extract_image,
    extract_raw_content,
    parse_struct_time,
    sanitize_html,
    strip_html_attributes,
)
from lib.ext.fastapi import BaseService
from schemas import FeedFetchResult, ParsedFeed, ParsedFeedEntry


class FeedParserService(BaseService):
    """
    Service for parsing feed responses and building feed entry data.
    """

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        super().__init__()

        self._client = http_client

    async def parse_response(self, url: str, response: httpx.Response) -> FeedFetchResult:
        try:
            parsed = await asyncio.to_thread(feedparser.parse, response.content)

            if parsed.bozo and not parsed.entries:
                return FeedFetchResult(
                    status=FeedFetchStatus.ERROR,
                    error_message=f"Feed parse error: {parsed.bozo_exception}",
                    error_is_transient=False,
                )

            if parsed.bozo:
                self.logger.warning(f"Feed {url}: bozo flag, partial data")

            feed_meta = ParsedFeed(
                title=sanitize_html(strip_html_attributes(parsed.feed.title or None)),
                description=sanitize_html(strip_html_attributes(parsed.feed.description or None)),
                site_url=parsed.feed.link or None,
                favicon_url=None,
            )

            entries = await self.process_entries(parsed.entries)

            return FeedFetchResult(
                status=FeedFetchStatus.OK,
                feed_meta=feed_meta,
                entries=entries,
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
            )
        except Exception as exc:
            self.logger.error(f"Unhandled error parsing {url}: {exc}")
            return FeedFetchResult(
                status=FeedFetchStatus.ERROR,
                error_message=str(exc),
                error_is_transient=True,
            )

    async def process_entries(self, raw_entries: list) -> list[ParsedFeedEntry]:
        tasks = [self._process_entry(entry) for entry in raw_entries]
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )
        entries: list[ParsedFeedEntry] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.debug(f"Entry {i} failed: {result}")
            elif isinstance(result, ParsedFeedEntry):
                entries.append(result)

        return entries

    async def _process_entry(self, entry) -> ParsedFeedEntry | None:
        guid = entry.get("id") or entry.get("link") or entry.get("title")
        if not guid:
            return None

        raw_content = sanitize_html(clean_html_attributes(extract_raw_content(entry)))
        summary = await self._resolve_summary(entry.get("summary"), entry.get("link"))

        full_content = await self._maybe_extract_full_text(raw_content, entry.get("link"))
        full_content = sanitize_html(clean_html_attributes(full_content)) if full_content else None
        final_content = full_content or raw_content

        if self._content_is_only_link(final_content):
            downstream_content = await self._fetch_article_body(entry.get("link"))
            final_content = downstream_content or final_content

        return ParsedFeedEntry(
            guid=guid,
            url=entry.get("link"),
            title=(sanitize_html(strip_html_attributes(entry.get("title"))) if entry.get("title") else None),
            summary=summary,
            content=final_content,
            author=entry.get("author"),
            image_url=extract_image(entry),
            published_at=parse_struct_time(entry.get("published_parsed")),
            updated_at=parse_struct_time(entry.get("updated_parsed") or entry.get("published_parsed")),
            content_hash=compute_content_hash(
                entry.get("title"),
                final_content,
                summary,
            ),
        )

    async def _resolve_summary(self, summary: str | None, url: str | None) -> str | None:
        if not summary:
            return url

        if self._contains_html(summary):
            if url:
                page_summary = await self._fetch_page_summary(url)
                if page_summary:
                    return page_summary
            return url

        return sanitize_html(strip_html_attributes(summary))

    async def _fetch_page_summary(self, url: str) -> str | None:
        try:
            response = await self._client.get(url, headers=FEED_FETCHER_HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for attr in ["og:description", "twitter:description", "description"]:
                meta = soup.find("meta", property=attr) or soup.find("meta", attrs={"name": attr})
                if meta and meta.get("content"):
                    return sanitize_html(clean_html_attributes(meta["content"]))

            return None
        except Exception as exc:
            self.logger.debug(f"Page summary fetch failed for {url}: {exc}")
            return None

    def _contains_html(self, value: str) -> bool:
        return bool(BeautifulSoup(value, "html.parser").find())

    def _content_is_only_link(self, content: str | None) -> bool:
        if not content:
            return True

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text(strip=True)
        if not text:
            return True

        if soup.find_all(True) == [soup.find("a")]:
            return True

        if text.startswith("http://") or text.startswith("https://"):
            return True

        return False

    async def _fetch_article_body(self, url: str | None) -> str | None:
        if not url:
            return None

        try:
            response = await self._client.get(url, headers=FEED_FETCHER_HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup.find_all(
                [
                    "script",
                    "style",
                    "noscript",
                    "iframe",
                    "form",
                    "input",
                    "button",
                    "header",
                    "footer",
                    "nav",
                    "aside",
                ]
            ):
                tag.decompose()

            article_body = soup.find("article") or soup.body or soup

            html = sanitize_html(strip_html_attributes(str(article_body)))
            return html
        except Exception as exc:
            self.logger.debug(f"Article body fetch failed for {url}: {exc}")
            return None

    async def _maybe_extract_full_text(self, raw_content: str | None, url: str | None) -> str | None:
        if raw_content and len(raw_content) >= FEED_FETCHER_THIN_CONTENT_THRESHOLD:
            return None

        if not url:
            return None

        try:
            response = await self._client.get(url, headers=FEED_FETCHER_HEADERS)
            response.raise_for_status()

            return await asyncio.to_thread(
                trafilatura.extract,
                response.text,
                include_comments=False,
                include_tables=True,
                output_format="html",
            )
        except Exception as exc:
            self.logger.debug(f"Full-text extraction failed for {url}: {exc}")
            return None
