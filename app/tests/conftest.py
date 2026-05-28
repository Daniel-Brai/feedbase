import asyncio
import os
from pathlib import Path

import pytest
from pydantic import PostgresDsn
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

os.environ["APP_ENVIRONMENT"] = "test"
os.environ["APP_POSTGRES_USER"] = "postgres"
os.environ["APP_POSTGRES_PASSWORD"] = "postgres"
os.environ["APP_POSTGRES_DB"] = f"feedbase_test_db_{os.environ.get('PYTEST_XDIST_WORKER', 'master')}"
os.environ["APP_SUPERUSER_EMAIL"] = "feedbase_admin@test.com"
os.environ["APP_SUPERUSER_PASSWORD"] = "TestPassword123!"


from settings import settings

TestAsyncDBEngine = create_async_engine(
    str(settings.APP_SQLALCHEMY_DATABASE_URI),
    poolclass=NullPool,
)

TestAsyncDBSession = async_scoped_session(
    async_sessionmaker(
        bind=TestAsyncDBEngine,
        class_=AsyncSession,
        expire_on_commit=False,
    ),
    scopefunc=asyncio.current_task,
)


@pytest.fixture
def test_support_data_dir() -> Path:
    return Path(__file__).parent / "support"


@pytest.fixture(scope="session", autouse=True)
def manage_test_database():
    connection_url = str(
        PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=settings.APP_POSTGRES_USER,
            password=settings.APP_POSTGRES_PASSWORD,
            host=settings.APP_POSTGRES_HOST,
            port=settings.APP_POSTGRES_PORT,
        )
    )

    with create_engine(url=connection_url, isolation_level="AUTOCOMMIT").connect() as connection:
        try:
            connection.execute(text(f"CREATE DATABASE {settings.APP_POSTGRES_DB}"))
        except ProgrammingError:
            connection.execute(text(f"DROP DATABASE {settings.APP_POSTGRES_DB}"))
            connection.execute(text(f"CREATE DATABASE {settings.APP_POSTGRES_DB}"))

    sync_engine = create_engine(str(settings.APP_SQLALCHEMY_DATABASE_SYNC_URI))
    try:
        with sync_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))

        SQLModel.metadata.create_all(bind=sync_engine)
    finally:
        sync_engine.dispose()

    yield

    with create_engine(url=connection_url, isolation_level="AUTOCOMMIT").connect() as connection:
        connection.execute(text(f"DROP DATABASE {settings.APP_POSTGRES_DB} WITH (FORCE)"))
