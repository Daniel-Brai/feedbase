from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from filters.article_status import ArticleStatusFilter
from lib.pagination import Filter, FilterDepends, with_prefix
from models.article import Article


class ArticleFilter(Filter):
    """
    Filter for article listing endpoints.
    """

    id: UUID | None = Field(default=None, description="Filter by exact ID")
    id__in: list[UUID] | None = Field(default=None, description="Filter by list of IDs")

    feed_id: UUID | None = Field(default=None, description="Filter by feed ID")
    feed_id__in: list[UUID] | None = Field(default=None, description="Filter by list of feed IDs")

    title: str | None = Field(default=None, description="Filter by exact title")
    title__ilike: str | None = Field(default=None, description="Filter by title pattern (case-insensitive)")

    author: str | None = Field(default=None, description="Filter by exact author")
    author__ilike: str | None = Field(default=None, description="Filter by author pattern (case-insensitive)")

    published_at__gt: datetime | None = Field(default=None, description="Filter articles published after this date")
    published_at__lt: datetime | None = Field(default=None, description="Filter articles published before this date")
    published_at__gte: datetime | None = Field(
        default=None, description="Filter articles published on or after this date"
    )
    published_at__lte: datetime | None = Field(
        default=None, description="Filter articles published on or before this date"
    )

    created_at: datetime | None = Field(default=None, description="Filter by exact creation date")

    created_at__gt: datetime | None = Field(default=None, description="Filter articles created after this date")
    created_at__lt: datetime | None = Field(default=None, description="Filter articles created before this date")

    search: str | None = Field(
        default=None,
        description="Perform search on articles using FTS and Fuzzy matching",
    )

    statuses: Optional[ArticleStatusFilter] = FilterDepends(with_prefix("statuses", ArticleStatusFilter))

    order_by: list[str] | None = ["-published_at"]

    class Constants(Filter.Constants):
        model = Article
        search_field_name = "search"
        search_trgm_fields = ["title", "author", "summary", "content"]
        search_model_fields = ["title", "author", "summary", "content"]
        allowed_sort_fields = [
            "title",
            "published_at",
            "created_at",
            "updated_at",
        ]
        default_order_by = "-published_at"
