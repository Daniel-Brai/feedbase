from enum import StrEnum


class OGType(StrEnum):
    """
    Enumeration of Open Graph types for SEO metadata.

    Attributes:
        WEBSITE (str, "website"): Represents a general website.
        ARTICLE (str, "article"): Represents an article or blog post.
        PROFILE (str, "profile"): Represents a person's profile.
    """

    WEBSITE = "website"
    ARTICLE = "article"
    PROFILE = "profile"
