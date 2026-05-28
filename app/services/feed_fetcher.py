from dataclasses import asdict
from datetime import UTC, datetime

import httpx
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from constants import FEED_FETCHER_HEADERS
from enums import FeedFetchStatus, FeedStatus
from lib.ext.fastapi import IORunnableService
from models import Feed
from repositories import ArticleRepository, FeedRepository
from schemas import FeedFetchHints, FeedFetchResult, ParsedFeedEntry
from services.feed_parser import FeedParserService
from settings import settings


class FeedFetcherService(IORunnableService):
    """
    Service for fetching and parsing feeds from URLs
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self._client = httpx.AsyncClient(timeout=httpx.Timeout(settings.APP_HTTP_CLIENT_TIMEOUT_SECONDS, connect=10.0))
        self.feed_repo = FeedRepository(db)
        self.article_repo = ArticleRepository(db)
        self.feed_parser_svc = FeedParserService(self._client)

    async def run(self, feed: Feed) -> tuple[int, int]:
        """
        Fetches and parses feeds from the given URLs

        Args:
            urls (list[str | HttpUrl]): A list of feed URLs to fetch and parse.

        Returns:
            tuple[int, int]: A tuple containing the number of new articles and the number of updated articles.

        **NOTE**: This service doesn't commit any changes as it is used with another service so it is up to the caller to commit or rollback the transaction.
        """

        feed_hints = FeedFetchHints(
            etag=feed.etag,
            last_modified=feed.last_modified,
        )
        result = await self._fetch(feed.url, feed_hints)

        if result.status == FeedFetchStatus.NOT_MODIFIED:
            await self.feed_repo.update_with_obj(feed, {"last_fetched_at": datetime.now(UTC)})
            return 0, 0

        if result.status == FeedFetchStatus.ERROR:
            update_data = {
                "last_fetched_at": datetime.now(UTC),
                "last_error": result.error_message,
                "error_count": feed.error_count + 1,
            }

            if feed.error_count >= 10:
                update_data["status"] = FeedStatus.DEAD
                self.logger.warning(f"Marking feed: {feed.url} as DEAD due to repeated errors.")
            elif feed.error_count >= 1:
                update_data["status"] = FeedStatus.FAILING
                self.logger.warning(f"Marking feed: {feed.url} as FAILING due to error: {result.error_message}")

            await self.feed_repo.update_with_obj(feed, update_data)

            return 0, 0

        parsed_feed = result.feed_meta

        if parsed_feed:
            update_data = {}
            if parsed_feed.title and parsed_feed.title != feed.title:
                update_data["title"] = parsed_feed.title
            if parsed_feed.description and parsed_feed.description != feed.description:
                update_data["description"] = parsed_feed.description
            if parsed_feed.site_url and parsed_feed.site_url != feed.site_url:
                update_data["site_url"] = parsed_feed.site_url
            if parsed_feed.favicon_url and parsed_feed.favicon_url != feed.favicon_url:
                update_data["favicon_url"] = parsed_feed.favicon_url

            if result.etag != feed.etag:
                update_data["etag"] = result.etag
            if result.last_modified != feed.last_modified:
                update_data["last_modified"] = result.last_modified

            if feed.status == FeedStatus.FAILING:
                update_data["status"] = FeedStatus.ACTIVE

            update_data["last_fetched_at"] = datetime.now(UTC)
            update_data["last_error"] = None
            update_data["error_count"] = 0

            if update_data:
                await self.feed_repo.update_with_obj(feed, update_data)

        if not result.entries:
            return 0, 0

        existing_feed_articles = await self.article_repo.get_all_articles_for_feed(feed.id)

        existing_articles_map = {art.guid: art for art in existing_feed_articles}

        new_articles = []
        updated_articles = []
        updated_article_ids = []

        for entry in result.entries:
            existing = existing_articles_map.get(entry.guid)
            if existing is None:
                data = asdict(entry)
                data["feed_id"] = feed.id
                new_articles.append(data)
            else:
                changed = False
                if entry.updated_at and existing.updated_at:
                    if entry.updated_at > existing.updated_at:
                        changed = True
                else:
                    if existing.content_hash != entry.content_hash:
                        changed = True

                if changed:
                    updated_article_ids.append(existing.id)
                    updated_articles.append(
                        {
                            "title": existing.title,
                            "summary": existing.summary,
                            "content": existing.content,
                            "author": existing.author,
                            "updated_at": existing.updated_at,
                            "content_hash": existing.content_hash,
                        }
                    )

        if new_articles:
            await self.article_repo.bulk_create(new_articles)

        if updated_articles:
            await self.article_repo.bulk_update(updated_article_ids, updated_articles)

        return len(new_articles), len(updated_articles)

    async def _fetch(self, url: str, hints: FeedFetchHints) -> FeedFetchResult:
        try:
            response = await self._http_get(url, hints)

            if response.status_code == status.HTTP_304_NOT_MODIFIED:
                self.logger.debug(f"Feed {url}: 304 Not Modified")
                return FeedFetchResult(status=FeedFetchStatus.NOT_MODIFIED)

            if response.status_code >= status.HTTP_400_BAD_REQUEST:
                transient = response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
                return FeedFetchResult(
                    status=FeedFetchStatus.ERROR,
                    error_message=f"HTTP {response.status_code}",
                    error_is_transient=transient,
                )

            return await self.feed_parser_svc.parse_response(url, response)
        except Exception as exc:
            self.logger.error(f"Unhandled error fetching {url}: {exc}")
            return FeedFetchResult(
                status=FeedFetchStatus.ERROR,
                error_message=str(exc),
                error_is_transient=True,
            )

    async def _http_get(self, url: str, hints: FeedFetchHints) -> httpx.Response:
        headers = {**FEED_FETCHER_HEADERS}
        if hints.etag:
            headers["If-None-Match"] = hints.etag

        if hints.last_modified:
            headers["If-Modified-Since"] = hints.last_modified

        return await self._client.get(url, headers=headers)

    async def process_entries(self, raw_entries: list) -> list[ParsedFeedEntry]:
        return await self.feed_parser_svc.process_entries(raw_entries)
