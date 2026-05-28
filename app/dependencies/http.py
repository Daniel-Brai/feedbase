from typing import Annotated

from fastapi import Depends, Request
from httpx import AsyncClient

from settings import settings


def get_http_client(request: Request) -> AsyncClient:
    """
    Dependency to retrieve the application's shared HTTP client from app.state.
    """

    client = getattr(request.app.state, "http_client", None)
    if client is None:
        return AsyncClient(timeout=settings.APP_HTTP_CLIENT_TIMEOUT_SECONDS, follow_redirects=True)

    return client


HttpClientDep = Annotated[AsyncClient, Depends(get_http_client)]
