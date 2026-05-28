from factory.declarations import LazyAttribute
from factory.faker import Faker

from enums import ArticleAnnotationKind
from lib.testing.database import AsyncSQLAlchemyFactory
from models import ArticleAnnotation
from tests.conftest import TestAsyncDBSession


class ArticleAnnotationFactory(AsyncSQLAlchemyFactory):
    user_id = LazyAttribute(
        lambda o: (o.user.id if getattr(o, "user", None) is not None else getattr(o, "user_id", None))
    )
    article_id = LazyAttribute(
        lambda o: (o.article.id if getattr(o, "article", None) is not None else getattr(o, "article_id", None))
    )
    kind = ArticleAnnotationKind.NOTES
    body = Faker("paragraph", nb_sentences=2)
    highlight_text = None
    highlight_start = None
    highlight_end = None
    color = None

    class Meta:  # type: ignore
        model = ArticleAnnotation
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
