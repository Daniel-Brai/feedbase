from datetime import datetime

from pydantic import BaseModel

from lib.ext.pydantic import optional
from models import ArticleStatus


class ArticleStatusCreate(BaseModel):
    """
    Schema for creating an article status

    Attributes:
        is_read (bool): Whether the article has been read by the user.
        is_starred (bool): Whether the article has been starred by the user.
        is_bookmarked (bool): Whether the article has been bookmarked by the user.
    """

    is_read: bool
    is_starred: bool
    is_bookmarked: bool


@optional
class ArticleStatusUpdate(ArticleStatusCreate):
    """
    Schema for updating an article status

    Attributes:
        is_read (bool | None): Whether the article has been read by the user.
        is_starred (bool | None): Whether the article has been starred by the user.
        is_bookmarked (bool | None): Whether the article has been bookmarked by the user.
    """

    pass


class ArticleStatusOut(BaseModel):
    """
    Schema for an article status.

    Attributes:
        is_read (bool): Whether the article has been read by the user.
        is_starred (bool): Whether the article has been starred by the user.
        is_bookmarked (bool): Whether the article has been bookmarked by the user.
        read_at (datetime | None): The timestamp when the article was marked as read, or None if it has not been marked as read.
        bookmarked_at (datetime | None): The timestamp when the article was marked as bookmarked, or None if it has not been marked as bookmarked.
    """

    is_read: bool = False
    is_starred: bool = False
    is_bookmarked: bool = False
    read_at: datetime | None = None
    bookmarked_at: datetime | None = None

    @classmethod
    def from_model(cls, model: ArticleStatus) -> "ArticleStatusOut":
        return cls(
            is_read=model.is_read,
            is_starred=model.is_starred,
            is_bookmarked=model.is_bookmarked,
            read_at=model.read_at,
            bookmarked_at=model.bookmarked_at,
        )
