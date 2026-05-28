from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from enums import FeedFetchStatus


@dataclass
class DiscoveredFeed:
    """
    Schema for a discovered feed, used during feed discovery before subscribing.

    Attributes:
        url (str): The URL of the discovered feed.
        title (str): The title of the discovered feed, if available.
        mime (str): The MIME type of the feed, if available.
        priority (Any): The priority of the feed based on its MIME type, used for sorting multiple discovered feeds from the same source.
    """

    url: str
    title: str
    mime: str
    priority: Any


@dataclass(frozen=True)
class FeedFetchHints:
    """
    Schema for feed fetch hints, used for conditional GETs.

    Attributes:
        etag (str | None): The ETag value from the previous fetch, if available.
        last_modified (str | None): The Last-Modified value from the previous fetch, if
    """

    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class ParsedFeedEntry:
    """
    Schema for a feed entry that has been parsed.

    Attributes:
        guid (str): A unique identifier for the entry, used for deduplication.
        url (str | None): The URL of the entry, if available.
        title (str | None): The title of the entry, if available.
        summary (str | None): A short summary of the entry, if available.
        content (str | None): The full content of the entry, if available. This may
                                be extracted using trafilatura if the original content is too short.
        author (str | None): The author of the entry, if available.
        image_url (str | None): A URL to an image associated with the entry, if available.
        published_at (str | None): The published date of the entry, if available.
        updated_at (str | None): The last updated date of the entry, if available.
        content_hash (str): A hash of the entry's content, used for change detection.
    """

    guid: str
    url: str | None
    title: str | None
    summary: str | None
    content: str | None
    author: str | None
    image_url: str | None
    published_at: datetime | None
    updated_at: datetime | None
    content_hash: str


@dataclass(frozen=True)
class ParsedFeed:
    """
    Schema for a feed that has been parsed.

    Attributes:
        title (str | None): The title of the feed, if available.
        description (str | None): A description of the feed, if available.
        site_url (str | None): The URL of the website associated with the feed, if available.
        favicon_url (str | None): A URL to the feed's favicon, if available
    """

    title: str | None
    description: str | None
    site_url: str | None
    favicon_url: str | None


@dataclass
class FeedFetchResult:
    """
    Schema for the result of a feed fetch operation.

    Attributes:
        status (FeedFetchStatus): The status of the fetch operation (e.g., SUCCESS, NOT_MODIFIED, ERROR).
        feed_meta (ParsedFeed | None): Metadata about the feed, if the fetch was successful
        entries (list[ParsedFeedEntry]): A list of parsed feed entries, if the fetch was successful.
        etag (str | None): The ETag value from the HTTP response, for use in future conditional GETs.
        last_modified (str | None): The Last-Modified value from the HTTP response, for use in future conditional GETs.
        error_message (str | None): An error message describing what went wrong, if the fetch failed.
        error_is_transient (bool): Whether the error is transient (e.g., network issue) or permanent (e.g., bad URL), used to determine retry behavior.
    """

    status: FeedFetchStatus
    feed_meta: ParsedFeed | None = None
    entries: list[ParsedFeedEntry] = field(default_factory=list)
    etag: str | None = None
    last_modified: str | None = None
    error_message: str | None = None
    error_is_transient: bool = True


class FeedDiscoverCreate(BaseModel):
    """
    Schema for discovering feed metadata before subscribing.

    Attributes:
        url (str | HttpUrl): The URL of the feed to discover.
    """

    url: str | HttpUrl = Field(
        ...,
        description="The URL of the feed to discover.",
        examples=["https://hnrss.github.io"],
    )


class FeedDiscoverOut(BaseModel):
    """
    Schema for the response from the feed discovery endpoint.

    Attributes:
        text (str): The title of the feed, if available.
        value (str | HttpUrl): The URL of the feed that was discovered.
    """

    text: str = Field(
        ...,
        description="The title of the feed, if available.",
        examples=["hrss.org updates"],
    )
    value: str | HttpUrl = Field(
        ...,
        description="The URL of the feed that was discovered.",
        examples=["https://hnrss.github.io"],
    )
