from uuid import UUID

from sqlmodel import TEXT, Column, Field

from enums import ArticleAnnotationKind
from lib.database.mixins import TimestampMixin, UUID7Mixin


class ArticleAnnotation(UUID7Mixin, TimestampMixin, table=True):
    """
    Represents a user annotation on an article, which can be either a note or a highlight.

    Attributes:
        id (UUID): Unique identifier for the annotation.
        user_id (int): ID of the user who created the annotation.
        article_id (int): ID of the annotated article.
        kind (ArticleAnnotationKind): Type of annotation (e.g., note or highlight).
        body (str | None): The text of the note (for notes) or the highlighted passage (for highlights).
        highlight_text (str | None): The exact text that was highlighted (for highlights).
        highlight_start (int | None): The character offset where the highlight starts in the article body (for highlights).
        highlight_end (int | None): The character offset where the highlight ends in the article body (for highlights).
        color (str | None): The hex code color of the highlight (for highlights)
    """

    user_id: int = Field(foreign_key="users.id")
    article_id: UUID = Field(foreign_key="articles.id")

    kind: ArticleAnnotationKind = Field(
        sa_column=Column(
            TEXT(),
            nullable=False,
            default=ArticleAnnotationKind.NOTES,
        )
    )

    body: str | None = Field(sa_column=Column(TEXT(), nullable=True, default=None))
    highlight_text: str | None = Field(sa_column=Column(TEXT(), nullable=True, default=None))
    highlight_start: int | None = None
    highlight_end: int | None = None

    color: str | None = None
