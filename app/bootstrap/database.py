from contextlib import asynccontextmanager

from lib.database import create_async_database_engine, create_async_session, db_async_session_manager
from lib.database.mixins import attach_slug_event_to_session
from settings import settings

DATABASE_URL = settings.APP_SQLALCHEMY_DATABASE_URI

engine_pool = create_async_database_engine(str(DATABASE_URL))
session_pool_factory = create_async_session(engine_pool)

engine = create_async_database_engine(str(DATABASE_URL), use_null_pool=True)
session_factory = create_async_session(engine)


@asynccontextmanager
async def get_db_pool():
    """
    Async context manager that yields a database session from the connection pool and ensures it's properly closed after use.
    """
    async with db_async_session_manager(session_pool_factory) as session:
        attach_slug_event_to_session(session)
        yield session


@asynccontextmanager
async def get_db():
    """
    Async context manager that yields a non-pooled database session and ensures it's properly closed after use.
    """

    async with db_async_session_manager(session_factory) as session:
        attach_slug_event_to_session(session)
        yield session
