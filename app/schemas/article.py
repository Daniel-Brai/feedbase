from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, NonNegativeInt

from models import Article

from .article_status import ArticleStatusOut


class ArticleStatsOut(BaseModel):
    """
    Schema for article status counts.

    Attributes:
        total (NonNegativeInt): The total number of articles.
        unread (NonNegativeInt): The number of unread articles.
        starred (NonNegativeInt): The number of starred articles.
        bookmarked (NonNegativeInt): The number of bookmarked articles.
        today (NonNegativeInt): The number of articles published today.
    """

    total: NonNegativeInt
    unread: NonNegativeInt
    starred: NonNegativeInt
    bookmarked: NonNegativeInt
    today: NonNegativeInt

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "ArticleStatsOut":
        return cls(
            total=data.get("total", 0),
            unread=data.get("unread", 0),
            starred=data.get("starred", 0),
            bookmarked=data.get("bookmarked", 0),
            today=data.get("today", 0),
        )


class ArticleOut(BaseModel):
    """
    Schema for an article response

    Attributes:
        id (UUID): The unique identifier of the article.
        feed_id (UUID): The unique identifier of the feed the article belongs to.
        feed_title (str | None): The display title of the feed, using the subscription title if provided.
        title (str | None): The title of the article.
        url (str | None): The URL of the article.
        author (str | None): The author of the article.
        published_at (datetime | None): The publication date of the article.
        summary (str | None): A summary of the article.
        content (str | None): The full content of the article.
        guid (str): The globally unique identifier of the article.
        status (ArticleStatusOut | None): The status of the article for the authenticated user, or None if the status is not available.
    """

    id: UUID
    feed_id: UUID
    feed_title: str | None = None
    title: str | None
    url: str | None
    author: str | None
    published_at: datetime | None
    summary: str | None
    content: str | None
    guid: str
    status: ArticleStatusOut | None = None

    @classmethod
    def from_model(cls, article: Article) -> "ArticleOut":
        """
        Create an `ArticleOut` instance from an `Article` model instance.
        """

        feed_title = None
        if article.feed and article.feed.subscriptions:
            feed_title = article.feed.subscriptions[0].title or getattr(article.feed, "title", None)

        status = None
        if article.statuses:
            article_status = article.statuses[0]
            status = ArticleStatusOut.from_model(article_status)

        return cls(
            id=article.id,
            feed_id=article.feed_id,
            feed_title=feed_title,
            title=article.title,
            url=str(article.url) if article.url else None,
            author=article.author,
            published_at=article.published_at,
            summary=article.summary,
            content=article.content,
            guid=article.guid,
            status=status,
        )
