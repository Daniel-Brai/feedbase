from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import TIMESTAMP, Column, Field, Relationship

from lib.database.mixins import UUID7Mixin

if TYPE_CHECKING:
    from models.article import Article
    from models.user import User


class ArticleStatus(
    UUID7Mixin,
    table=True,
):
    """
    Represents the status of an article for a specific user.

    Attributes:
        id (UUID): The unique identifier for the article status, generated using the UUID7Mixin.
        article_id (UUID): The ID of the article.
        user_id (int): The ID of the user.
        is_read (bool): Whether the article has been read by the user.
        is_starred (bool): Whether the article has been starred by the user.
        is_bookmarked (bool): Whether the article has been bookmarked by the user.
        read_at (datetime | None): The timestamp when the article was marked as read.
        bookmarked_at (datetime | None): The timestamp when the article was marked as bookmarked.
    """

    __table_args__ = (UniqueConstraint("article_id", "user_id", name="uq_article_status_article_user"),)

    article_id: UUID = Field(
        index=True,
        foreign_key="articles.id",
        description="The ID of the article.",
    )
    user_id: int = Field(
        index=True,
        foreign_key="users.id",
        ondelete="CASCADE",
        description="The ID of the user.",
    )
    is_read: bool = Field(
        default=False,
        description="Whether the article has been read by the user.",
    )
    is_starred: bool = Field(
        default=False,
        description="Whether the article has been starred by the user.",
    )
    is_bookmarked: bool = Field(
        default=False,
        description="Whether the article has been bookmarked by the user.",
    )
    read_at: datetime | None = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True, default=None),
        description="The timestamp when the article was marked as read.",
    )
    bookmarked_at: datetime | None = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True, default=None),
        description="The timestamp when the article was marked as bookmarked.",
    )

    user: "User" = Relationship(back_populates="article_statuses")
    article: "Article" = Relationship(back_populates="statuses")
