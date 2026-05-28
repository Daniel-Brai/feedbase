from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from enums import ArticleAnnotationKind
from lib.ext.pydantic import optional
from models import ArticleAnnotation


class ArticleAnnotationCreate(BaseModel):
    """
    Schema for creating a new article annotation.

    Attributes:
        article_id (UUID): The ID of the article being annotated.
        kind (ArticleAnnotationKind): The kind of annotation, either a note or a highlight.
        body (str | None): The text body of the annotation.
        highlight_text (str | None): The highlighted text when the annotation is a highlight.
        highlight_start (int | None): The starting offset of the highlight.
        highlight_end (int | None): The ending offset of the highlight.
        color (str | None): Optional color value for the annotation.
    """

    article_id: UUID = Field(..., description="The ID of the article being annotated.")
    kind: ArticleAnnotationKind = Field(
        default=ArticleAnnotationKind.NOTES,
        description="The kind of annotation, either a note or a highlight.",
    )
    body: str | None = Field(
        None,
        description="The text body of the annotation.",
    )
    highlight_text: str | None = Field(
        None,
        description="The highlighted text when the annotation is a highlight.",
    )
    highlight_start: int | None = Field(
        None,
        description="The starting offset of the highlight.",
    )
    highlight_end: int | None = Field(
        None,
        description="The ending offset of the highlight.",
    )
    color: str | None = Field(
        None,
        description="Optional color value for the annotation.",
    )


@optional(exclude_fields=["article_id"])
class ArticleAnnotationUpdate(ArticleAnnotationCreate):
    """
    Schema for updating an article annotation.

    All fields are optional, allowing partial updates.
    """

    pass


class ArticleAnnotationOut(BaseModel):
    """
    Schema for returning an article annotation.

    Attributes:
        id (UUID): The unique identifier of the annotation.
        article_id (UUID): The ID of the annotated article.
        kind (ArticleAnnotationKind): The kind of annotation.
        body (str | None): The text body of the annotation.
        highlight_text (str | None): The highlighted text.
        highlight_start (int | None): The starting offset of the highlight.
        highlight_end (int | None): The ending offset of the highlight.
        color (str | None): Color associated with the annotation.
        created_at (datetime): When the annotation was created.
        updated_at (datetime | None): When the annotation was last updated.
    """

    id: UUID
    article_id: UUID
    kind: ArticleAnnotationKind
    body: str | None = None
    highlight_text: str | None = None
    highlight_start: int | None = None
    highlight_end: int | None = None
    color: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_model(cls, model: ArticleAnnotation) -> "ArticleAnnotationOut":
        return cls(
            id=model.id,
            article_id=model.article_id,
            kind=model.kind,
            body=model.body,
            highlight_text=model.highlight_text,
            highlight_start=model.highlight_start,
            highlight_end=model.highlight_end,
            color=model.color,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
