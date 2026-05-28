from factory.declarations import LazyAttribute

from lib.testing.database import AsyncSQLAlchemyFactory
from models import ArticleStatus
from tests.conftest import TestAsyncDBSession


class ArticleStatusFactory(AsyncSQLAlchemyFactory):
    user_id = LazyAttribute(
        lambda o: (o.user.id if getattr(o, "user", None) is not None else getattr(o, "user_id", None))
    )
    article_id = LazyAttribute(
        lambda o: (o.article.id if getattr(o, "article", None) is not None else getattr(o, "article_id", None))
    )
    is_read = False
    is_starred = False
    is_bookmarked = False
    read_at = None
    bookmarked_at = None

    class Meta:  # type: ignore
        model = ArticleStatus
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
