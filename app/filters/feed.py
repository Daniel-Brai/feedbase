from datetime import datetime
from uuid import UUID

from pydantic import Field

from enums.feed import FeedFormat, FeedStatus
from lib.pagination import Filter
from models.feed import Feed


class FeedFilter(Filter):
    """
    Filter for feed listing endpoints.

    This filter allows clients to specify pagination filters to filters against the feed

    It inherits from the base :class:`Filter` class, which provides common pagination functionality.

    Usage::

        # Example usage in a controller method
        @get("/feeds")
        async def list_feeds(self, filter: Annotated[FeedFilter, FilterDepends(FeedFilter)]):
            ...
    """

    id: UUID | None = Field(default=None, description="Filter by ID")
    id__in: list[str] | None = Field(default=None, description="Filter by list of IDs")

    title: str | None = Field(default=None, description="Filter by exact title")
    title__ilike: str | None = Field(default=None, description="Filter by title pattern (case-insensitive)")

    url: str | None = Field(default=None, description="Filter by exact url")
    url__ilike: str | None = Field(default=None, description="Filter by url pattern (case-insensitive)")

    format: FeedFormat | None = Field(default=None, description="Filter by feed format")
    status: FeedStatus | None = Field(default=None, description="Filter by feed status")

    created_at__gt: datetime | None = Field(default=None, description="Filter feeds created after this date")
    created_at__lt: datetime | None = Field(default=None, description="Filter feeds created before this date")
    created_at__gte: datetime | None = Field(default=None, description="Filter feeds created on or after this date")
    created_at__lte: datetime | None = Field(default=None, description="Filter feeds created on or before this date")

    updated_at__gt: datetime | None = Field(default=None, description="Filter feeds updated after this date")
    updated_at__lt: datetime | None = Field(default=None, description="Filter feeds updated before this date")

    search: str | None = Field(default=None, description="Perform search on feeds using FTS and Fuzzy matching")

    order_by: list[str] | None = ["-created_at"]

    class Constants(Filter.Constants):
        model = Feed
        search_field_name = "search"
        search_trgm_fields = ["title", "url", "description"]
        search_model_fields = ["title", "url", "description"]
        allowed_sort_fields = [
            "title",
            "url",
            "description",
            "format",
            "status",
            "last_fetched_at",
            "error_count",
            "created_at",
            "updated_at",
        ]
        default_order_by = "-created_at"
