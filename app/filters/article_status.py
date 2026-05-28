from datetime import datetime
from typing import Annotated

from pydantic import BeforeValidator, Field

from lib.pagination import Filter
from lib.validators import validate_bool
from models.article_status import ArticleStatus


class ArticleStatusFilter(Filter):
    """
    Filter for article statuses.
    """

    is_read: Annotated[bool, BeforeValidator(validate_bool())] | None = Field(
        default=None, description="Filter by read status"
    )
    is_starred: Annotated[bool, BeforeValidator(validate_bool())] | None = Field(
        default=None, description="Filter by starred status"
    )
    is_bookmarked: Annotated[bool, BeforeValidator(validate_bool())] | None = Field(
        default=None, description="Filter by bookmarked status"
    )

    read_at__gt: datetime | None = Field(default=None, description="Filter by read after this date")
    read_at__lt: datetime | None = Field(default=None, description="Filter by read before this date")

    bookmarked_at__gt: datetime | None = Field(default=None, description="Filter by bookmarked after this date")
    bookmarked_at__lt: datetime | None = Field(default=None, description="Filter by bookmarked before this date")

    class Constants(Filter.Constants):
        model = ArticleStatus
        allowed_sort_fields = ["read_at", "bookmarked_at"]
