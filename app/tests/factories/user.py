from factory.declarations import LazyAttribute, LazyFunction
from factory.faker import Faker

from helpers import generate_fever_key
from lib.auth.security import Hasher
from lib.auth.user import generate_salt
from lib.testing.database import AsyncSQLAlchemyFactory
from models import User
from tests.conftest import TestAsyncDBSession


class UserFactory(AsyncSQLAlchemyFactory):

    email = Faker("email")
    name = Faker("name")
    bio = Faker("paragraph", nb_sentences=3)
    avatar = None
    password_salt = LazyFunction(lambda: generate_salt())
    hashed_password = LazyAttribute(lambda o: Hasher.hash("password", o.password_salt))
    email_verified = False
    is_active = True
    is_suspended = False
    roles = LazyFunction(list)
    permissions = LazyFunction(list)
    fever_key = LazyAttribute(lambda o: generate_fever_key(o.email, "password"))
    preferences = LazyFunction(dict)

    class Meta:  # type: ignore
        model = User
        sqlalchemy_session_factory = TestAsyncDBSession
        sqlalchemy_session_persistence = "commit"
