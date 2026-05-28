from factory.declarations import LazyAttribute

from lib.testing import AsyncSQLAlchemyFactory
from models import FeedSubscription
from tests.conftest import TestAsyncDBSession


class FeedSubscriptionFactory(AsyncSQLAlchemyFactory):
    title = None
    user_id = LazyAttribute(
        lambda o: (o.user.id if getattr(o, "user", None) is not None else getattr(o, "user_id", None))
    )
    feed_id = LazyAttribute(
        lambda o: (o.feed.id if getattr(o, "feed", None) is not None else getattr(o, "feed_id", None))
    )
    folder_id = LazyAttribute(lambda o: (o.folder.id if getattr(o, "folder", None) is not None else None))

    class Meta:  # type: ignore
        model = FeedSubscription
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
