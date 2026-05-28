from typing import Annotated

from fastapi import Depends

from services import FeedDiscoveryService, FeedSubscriptionService

from .database import AsyncDBSessionDep
from .http import HttpClientDep


def get_feed_discovery_service(http_client: HttpClientDep, db: AsyncDBSessionDep) -> FeedDiscoveryService:
    """
    Dependency provider for `FeedDiscoveryService`.
    """

    return FeedDiscoveryService(http_client, db)


def get_feed_subscription_service(db: AsyncDBSessionDep) -> FeedSubscriptionService:
    """
    Dependency provider for `FeedSubscriptionService`.
    """

    return FeedSubscriptionService(db)


FeedDiscoveryServiceDep = Annotated[FeedDiscoveryService, Depends(get_feed_discovery_service)]

FeedSubscriptionServiceDep = Annotated[FeedSubscriptionService, Depends(get_feed_subscription_service)]
