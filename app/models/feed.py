from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Index, text
from sqlmodel import TEXT, TIMESTAMP, VARCHAR, Column, Field, Relationship

from enums import FeedFormat, FeedStatus
from lib.database.mixins import TimestampMixin, UUID7Mixin

if TYPE_CHECKING:
    from models.article import Article
    from models.feed_subscription import FeedSubscription


class Feed(
    UUID7Mixin,
    TimestampMixin,
    table=True,
):
    """
    Represents an RSS/Atom feed that is to be fetched and parsed.

    Attributes:
        id (UUID): The unique identifier for the feed, generated using the UUID7Mixin.
        url (str): The URL of the feed to be fetched and parsed. e.g https://example.com/rss.xml
        site_url (str | None): The URL of the site associated with the feed. e.g https://example.com
        title (str): The title of the feed.
        description (str | None): A description of the feed.
        favicon_url (str | None): The URL of the feed's favicon.
        format (FeedFormat): The format of the feed (e.g. RSS, Atom).
        status (FeedStatus): The status of the feed (e.g. active, inactive).
        etag (str | None): The ETag header value from the last fetch, used for conditional requests.
        last_modified (str | None): The Last-Modified header value from the last fetch, used for conditional requests.
        last_fetched_at (datetime | None): The datetime when the feed was last fetched.
        last_error (str | None): The error message from the last fetch attempt, if any.
        error_count (int): The number of consecutive errors encountered while fetching the feed.
    """

    __table_args__ = (
        Index(
            "ix_feeds_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
            postgresql_where=text("title IS NOT NULL"),
        ),
        Index(
            "ix_feeds_description_trgm",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
            postgresql_where=text("description IS NOT NULL"),
        ),
        Index(
            "ix_feeds_url_trgm",
            "url",
            postgresql_using="gin",
            postgresql_ops={"url": "gin_trgm_ops"},
            postgresql_where=text("url IS NOT NULL"),
        ),
        Index("ix_feeds_status", "status"),
    )

    url: str = Field(
        index=True,
        unique=True,
        description="The URL of the feed to be fetched and parsed. e.g https://example.com/rss.xml",
    )
    site_url: str | None = Field(
        description="The URL of the site associated with the feed. e.g https://example.com",
    )
    title: str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="The title of the feed. It may be null if the feed has not been fetched and parsed yet, or if the feed does not provide a title.",
    )
    description: str | None = Field(sa_column=Column(TEXT, nullable=True, default=None))
    favicon_url: str | None = Field(sa_column=Column(TEXT, nullable=True, default=None))
    is_spark: bool = Field(
        default=False,
        index=True,
        description="Whether this feed is a Fever spark feed.",
    )

    format: FeedFormat = Field(
        sa_column=Column(
            TEXT,
            nullable=False,
            default=FeedFormat.RSS,
        )
    )
    status: FeedStatus = Field(
        sa_column=Column(
            TEXT,
            nullable=False,
            default=FeedStatus.ACTIVE,
        )
    )
    etag: str | None = Field(sa_column=Column(VARCHAR(255), nullable=True, default=None))
    last_modified: str | None = Field(sa_column=Column(VARCHAR(255), nullable=True, default=None))
    last_fetched_at: datetime | None = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=True, default=None))
    last_error: str | None = Field(sa_column=Column(TEXT, nullable=True, default=None))
    error_count: int = Field(default=0, nullable=False)

    articles: list["Article"] = Relationship(
        back_populates="feed", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    subscriptions: list["FeedSubscription"] = Relationship(
        back_populates="feed", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
