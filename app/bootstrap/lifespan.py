from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import FastAPI

from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Lifespan context manager for FastAPI application.
    """

    from httpx import AsyncClient

    from bootstrap.database import engine, engine_pool
    from bootstrap.redis import redis_connection_pool
    from lib.ext.stdlib import delete_attribute
    from lib.jobs import get_adapter

    to_thread.current_default_thread_limiter().total_tokens = 60

    adapter = get_adapter()
    adapter.start()

    async with AsyncClient(timeout=settings.APP_HTTP_CLIENT_TIMEOUT_SECONDS, follow_redirects=True) as client:
        app.state.http_client = client
        yield

    delete_attribute(app.state, "http_client")

    adapter.stop()

    await engine.dispose()
    await engine_pool.dispose()
    await redis_connection_pool.aclose()
