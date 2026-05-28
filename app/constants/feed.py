from settings import settings

FEED_TYPES_RELEVANCE = {
    "application/atom+xml": 1,
    "application/rss+xml": 2,
    "application/json": 3,
    "application/feed+json": 3,
}

FEED_TYPES = set(FEED_TYPES_RELEVANCE.keys())


FEED_FETCHER_HEADERS = {
    "User-Agent": settings.APP_USER_AGENT,
    "Accept": "application/rss+xml, application/atom+xml, application/json, text/xml, */*",
}


FEED_FETCHER_THIN_CONTENT_THRESHOLD = 500
