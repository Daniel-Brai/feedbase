from typing import Annotated

from fastapi import Body

from dependencies import AuthDep, FeedDiscoveryServiceDep, HttpClientDep
from lib.ext.fastapi import Controller, IResponse, ORJSONResponse, before_action, post
from schemas import FeedDiscoverCreate, FeedDiscoverOut
from settings import settings


class FeedController(Controller):
    """
    API Controller for managing feed-related API endpoints.
    """

    prefix = f"{settings.API_V1_STR}/feeds"

    @before_action
    def authenticate(self, user: AuthDep):
        """
        Dependency to ensure that the user is authenticated before accessing feed-related endpoints.
        """
        self.current_user = user

    @post(
        "/discover",
        operation_id="discover_feeds",
        response_model=IResponse[list[FeedDiscoverOut], None],
    )
    async def discover_feeds(
        self,
        body: Annotated[
            FeedDiscoverCreate,
            Body(..., description="The URL of the feed to discover."),
        ],
        http_client: HttpClientDep,
        service: FeedDiscoveryServiceDep,
    ) -> ORJSONResponse:
        """
        Discover feeds by passing a URL before the feed is added as a subscription.
        """

        message, data, metadata = await service.run(http_client, body)
        return self.json(
            message=message,
            data=data,
            metadata=metadata,
        )
