from datetime import datetime
from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from pydantic import HttpUrl
from sqlmodel import TEXT, TIMESTAMP, VARCHAR, Column, Field, Index, Relationship, UniqueConstraint, func, text

from lib.database.mixins import SlugConfig, SluggedMixin, TimestampMixin, UUID7Mixin

if TYPE_CHECKING:
    from models.article_status import ArticleStatus
    from models.feed import Feed


class Article(
    UUID7Mixin,
    SluggedMixin,
    TimestampMixin,
    table=True,
):
    """
    Represents an article parsed from a feed.

    Attributes:
        id (UUID): The unique identifier for the article, generated using the UUID7Mixin.
        feed_id (str): The ID of the feed this article belongs to.
        title (str): The title of the article.
        url (str): The URL of the article.
        author (str | None): The author of the article.
        published (datetime | None): The publication date of the article.
        summary (str | None): A summary or description of the article.
        content (str | None): The full content of the article.
        guid (str | None): A unique identifier for the article, often provided by the feed.
    """

    __table_args__ = (
        UniqueConstraint("feed_id", "guid", name="uq_article_feed_guid"),
        Index(
            "ix_articles_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
            postgresql_where=text("title IS NOT NULL"),
        ),
        Index("ix_articles_feed_published", "feed_id", "published_at"),
    )

    slug_config: ClassVar[SlugConfig] = SlugConfig(
        from_fields=["title", "guid", "feed_id"],
        update_on_change=True,
    )

    feed_id: UUID = Field(
        index=True,
        foreign_key="feeds.id",
        description="The ID of the feed this article belongs to.",
    )
    guid: str = Field(
        index=True,
        description="A unique identifier for the article, often provided by the feed.",
    )
    title: str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="The title of the article.",
    )
    summary: str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="A summary or description of the article.",
    )
    slug: str | None = Field(
        default=None,
        unique=True,
        index=True,
        description="URL-friendly slug generated for the article.",
    )
    url: HttpUrl | str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="The URL of the article.",
    )
    author: str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="The author of the article.",
    )
    image_url: HttpUrl | str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="The URL of the article's main image.",
    )
    content: str | None = Field(
        sa_column=Column(TEXT, nullable=True, default=None),
        description="The full content of the article.",
    )
    content_hash: str | None = Field(
        sa_column=Column(VARCHAR(64), nullable=True, default=None),
        description="A hash of the article content, used for deduplication.",
    )
    published_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, index=True, server_default=func.now()),
        description="The publication date of the article.",
    )

    feed: "Feed" = Relationship(back_populates="articles")
    statuses: list["ArticleStatus"] = Relationship(
        back_populates="article", sa_relationship_kwargs={"lazy": "selectin"}
    )
