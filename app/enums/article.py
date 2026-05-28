from enum import StrEnum


class ArticleAnnotationKind(StrEnum):
    """
    Enumeration for the kind of article annotation, either a freestanding note or a highlight with an optional note.

    Attributes:
        NOTES (str, "note"): Represents a freestanding note annotation.
        HIGHLIGHT (str, "highlight"): Represents a highlight annotation, which may include an optional note.
    """

    NOTES = "note"
    HIGHLIGHT = "highlight"
