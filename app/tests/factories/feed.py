from datetime import UTC, datetime
from uuid import uuid4

from factory.declarations import LazyFunction
from factory.faker import Faker

from enums import FeedFormat, FeedStatus
from lib.testing.database import AsyncSQLAlchemyFactory
from models import Feed
from tests.conftest import TestAsyncDBSession


class FeedFactory(AsyncSQLAlchemyFactory):

    url = LazyFunction(lambda: f"https://example.com/feeds/{uuid4().hex}")
    site_url = Faker("url", schemes=["https"])
    title = Faker("sentence", nb_words=3)
    description = Faker("paragraph", nb_sentences=2)
    favicon_url = LazyFunction(lambda: "https://example.com/favicon.ico")
    format = FeedFormat.RSS
    status = FeedStatus.ACTIVE
    egtag = LazyFunction(lambda: f'W/"{uuid4().hex}"')
    last_modified = LazyFunction(lambda: datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"))
    last_fetched_at = LazyFunction(lambda: datetime.now(UTC))
    last_error = None
    error_count = 0

    class Meta:  # type: ignore
        model = Feed
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
