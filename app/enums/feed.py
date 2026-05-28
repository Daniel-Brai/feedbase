from enum import StrEnum


class FeedFormat(StrEnum):
    """
    Enumeration of feed formats supported by the application.

    Attributes:
        RSS (str, "rss"): Represents the RSS feed format.
        ATOM (str, "atom"): Represents the Atom feed format.
        JSON (str, "json"): Represents the JSON feed format.
    """

    RSS = "rss"
    ATOM = "atom"
    JSON = "json"


class FeedStatus(StrEnum):
    """
    Enumeration of feed statuses used to indicate the health and activity of a feed.

    Attributes:
        ACTIVE (str, "active"): Indicates that the feed is active and functioning properly.
        FAILING (str, "failing"): Indicates that the feed is experiencing issues, such as parsing errors or connectivity problems.
        DEAD (str, "dead"): Indicates that the feed is no longer active, possibly due to persistent failures or the feed being removed by the source.
    """

    ACTIVE = "active"
    FAILING = "failing"
    DEAD = "dead"


class FeedFetchStatus(StrEnum):
    """
    Enumeration of feed fetch statuses used to indicate the result of a feed fetching operation.

    Attributes:
        OK (str, "ok"): Indicates that the feed was fetched and parsed successfully.
        NOT_MODIFIED (str, "not_modified"): Indicates that the feed has not changed since
                                            the last fetch (HTTP 304 Not Modified).
        ERROR (str, "error"): Indicates that an error occurred during fetching or parsing the feed, such as network issues or invalid feed format.
    """

    OK = "ok"
    NOT_MODIFIED = "not_modified"
    ERROR = "error"
