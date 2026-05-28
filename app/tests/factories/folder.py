from factory.declarations import LazyAttribute
from factory.faker import Faker

from lib.testing.database import AsyncSQLAlchemyFactory
from models import Folder
from tests.conftest import TestAsyncDBSession


class FolderFactory(AsyncSQLAlchemyFactory):
    name = Faker("word")
    user_id = LazyAttribute(
        lambda o: (o.user.id if getattr(o, "user", None) is not None else getattr(o, "user_id", None))
    )
    parent = None

    class Meta:  # type: ignore
        model = Folder
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
