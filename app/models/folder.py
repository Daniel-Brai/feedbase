from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import VARCHAR, Column, Field, Relationship

from lib.database.mixins import TimestampMixin, UUID7Mixin

if TYPE_CHECKING:
    from models.feed_subscription import FeedSubscription
    from models.user import User


class Folder(
    UUID7Mixin,
    TimestampMixin,
    table=True,
):
    """
    Represents a folder that can contain multiple subscriptions.

    Attributes:
        name (str): The name of the folder.
        user_id (int): The ID of the user who owns the folder.
        parent_id (UUID | None): The ID of the parent folder, if this is a subfolder.
    """

    __table_args__ = (
        UniqueConstraint("user_id", "name", "parent_id", name="uq_folder_user_name_parent"),
        Index(
            "uq_folders_root_name",
            "user_id",
            "name",
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
        Index(
            "ix_folders_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    name: str = Field(
        sa_column=Column(VARCHAR(500), nullable=False),
        description="The name of the folder.",
    )
    slug: str | None = Field(
        default=None,
        unique=True,
        index=True,
        description="URL-friendly slug generated for the folder.",
    )
    user_id: int = Field(
        foreign_key="users.id",
        index=True,
        description="The ID of the user who owns the folder.",
        ondelete="CASCADE",
    )
    parent_id: UUID | None = Field(
        foreign_key="folders.id",
        nullable=True,
        index=True,
        default=None,
        description="The ID of the parent folder, if this is a subfolder.",
        ondelete="SET NULL",
    )

    user: "User" = Relationship(back_populates="folders")
    subscriptions: list["FeedSubscription"] = Relationship(back_populates="folder")
    parent: Optional["Folder"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Folder.id"}
    )
    children: list["Folder"] = Relationship(back_populates="parent")
