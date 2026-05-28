from datetime import UTC, datetime
from uuid import uuid4

from factory.declarations import LazyAttribute, LazyFunction
from factory.faker import Faker

from helpers.feed import compute_content_hash
from lib.testing.database import AsyncSQLAlchemyFactory
from models import Article
from tests.conftest import TestAsyncDBSession


class ArticleFactory(AsyncSQLAlchemyFactory):
    feed_id = LazyAttribute(
        lambda o: (o.feed.id if getattr(o, "feed", None) is not None else getattr(o, "feed_id", None))
    )
    guid = LazyFunction(lambda: uuid4().hex)
    title = Faker("sentence", nb_words=6)
    summary = Faker("paragraph", nb_sentences=2)
    url = Faker("url", schemes=["https"])
    author = Faker("name")
    image_url = Faker("url", schemes=["https"])
    content = Faker("paragraph", nb_sentences=4)
    content_hash = LazyAttribute(lambda o: compute_content_hash(o.title, o.content, o.summary))
    published_at = LazyFunction(lambda: datetime.now(UTC))

    class Meta:  # type: ignore
        model = Article
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
