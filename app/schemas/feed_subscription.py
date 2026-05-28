from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from enums import FeedStatus


class FeedSubscriptionCreate(BaseModel):
    """
    Schema for creating a feed subscription.

    Attributes:
        urls (list[HttpUrl]): A list of feed URLs to subscribe to.
    """

    urls: list[HttpUrl | str] = Field(
        ...,
        description="A list of feed URLs to subscribe to.",
        examples=[["https://hnrss.github.io"]],
    )


class FeedSubscriptionUpdate(BaseModel):
    """
    Schema for updating a feed subscription.

    Attributes:
        title (str | None): An optional title for the subscription, set by the user. If not provided, the feed's title will be used.
        folder_id (UUID | None): The ID of the folder this subscription is in, if any.
    """

    title: str | None = Field(
        None,
        description="An optional title for the subscription, set by the user. If not provided, the feed's title will be used.",
        examples=["My HN Subscription"],
    )

    folder_id: UUID | None = Field(
        None,
        description="The ID of the folder this subscription is in, if any.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class FeedSubscriptionFeedOut(BaseModel):
    """
    Schema for a feed subscription, used in the list feeds response.

    Attributes:
        id (UUID): The unique identifier of the feed subscription.
        feed_id (UUID): The unique identifier of the associated feed.
        name (str | None): The name of the feed, if available.
        url (str | HttpUrl): The URL of the feed.
        status (FeedStatus): The status of the feed (e.g., active, inactive).
        last_fetched_at (datetime | None): The datetime when the feed was last fetched, if available.
    """

    id: UUID
    feed_id: UUID
    name: str | None
    url: str | HttpUrl
    status: FeedStatus
    last_fetched_at: datetime | None


class FeedSubscriptionOut(BaseModel):
    """
    Schema for a folder containing feed subscriptions.

    Attributes:
        id (UUID | None): The unique identifier of the folder, or None for uncategorized feeds.
        name (str): The name of the folder, or "Uncategorized" for feeds without a folder.
        feeds (list[FeedSubscriptionOut]): A list of feed subscriptions that belong to this folder.
    """

    id: UUID | None
    name: str
    feeds: list[FeedSubscriptionFeedOut]
