from datetime import datetime

from pydantic import Field

from lib.pagination import Filter
from models.user import User


class UserFilter(Filter):
    """
    Filter for user listing endpoints.
    """

    id: int | None = Field(default=None, description="Filter by exact ID")
    id__in: list[int] | None = Field(default=None, description="Filter by list of IDs")

    uuid: str | None = Field(default=None, description="Filter by exact UUID")
    uuid__in: list[str] | None = Field(default=None, description="Filter by list of UUIDs")

    name: str | None = Field(default=None, description="Filter by exact name")
    name__ilike: str | None = Field(default=None, description="Filter by name pattern (case-insensitive)")

    email: str | None = Field(default=None, description="Filter by exact email")
    email__ilike: str | None = Field(default=None, description="Filter by email pattern (case-insensitive)")

    bio: str | None = Field(default=None, description="Filter by exact bio")
    bio__ilike: str | None = Field(default=None, description="Filter by bio pattern (case-insensitive)")

    is_active: bool | None = Field(default=None, description="Filter by active status")
    is_suspended: bool | None = Field(default=None, description="Filter by suspended status")

    created_at__gt: datetime | None = Field(default=None, description="Filter users created after this date")
    created_at__lt: datetime | None = Field(default=None, description="Filter users created before this date")
    created_at__gte: datetime | None = Field(default=None, description="Filter users created on or after this date")
    created_at__lte: datetime | None = Field(default=None, description="Filter users created on or before this date")

    updated_at__gt: datetime | None = Field(default=None, description="Filter users updated after this date")
    updated_at__lt: datetime | None = Field(default=None, description="Filter users updated before this date")

    search: str | None = Field(default=None, description="Perform search on users using FTS and fuzzy matching")

    order_by: list[str] | None = ["name"]

    class Constants(Filter.Constants):
        model = User
        search_field_name = "search"
        search_model_fields = ["name", "email"]
        search_trgm_fields = ["name", "email"]
        allowed_sort_fields = [
            "name",
            "email",
            "uuid",
            "is_active",
            "is_suspended",
            "created_at",
            "updated_at",
        ]
        default_order_by = "name"
