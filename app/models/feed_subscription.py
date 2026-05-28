from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import VARCHAR, Column, Field, Relationship

from lib.database.mixins import TimestampMixin, UUID7Mixin

if TYPE_CHECKING:
    from models.feed import Feed
    from models.folder import Folder
    from models.user import User


class FeedSubscription(
    UUID7Mixin,
    TimestampMixin,
    table=True,
):
    """
    Represents a subscription to a feed.

    Attributes:
        title (str | None): An optional title for the subscription, set by the user. If not provided, the feed's title will be used.
        feed_id (UUID): The ID of the feed being subscribed to.
        folder_id (UUID | None): The ID of the folder this subscription is in, if any.
        user_id (int): The ID of the user who is subscribing to the feed.
    """

    __table_args__ = (UniqueConstraint("feed_id", "user_id", name="uq_feed_subscription_feed_user"),)

    title: str | None = Field(
        description="An optional title for the subscription, set by the user. If not provided, the feed's title will be used.",
        sa_column=Column(VARCHAR(500), nullable=True, default=None),
    )
    feed_id: UUID = Field(
        foreign_key="feeds.id",
        index=True,
        description="The ID of the feed being subscribed to.",
        ondelete="CASCADE",
    )
    folder_id: UUID | None = Field(
        foreign_key="folders.id",
        index=True,
        nullable=True,
        default=None,
        description="The ID of the folder this subscription is in, if any.",
        ondelete="SET NULL",
    )
    user_id: int = Field(
        foreign_key="users.id",
        index=True,
        description="The ID of the user who is subscribing to the feed.",
        ondelete="CASCADE",
    )

    user: "User" = Relationship(back_populates="feed_subscriptions")
    feed: "Feed" = Relationship(back_populates="subscriptions")
    folder: Optional["Folder"] = Relationship(back_populates="subscriptions")
