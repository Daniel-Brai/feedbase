from typing import Annotated, cast
from uuid import UUID

from fastapi import Body, Depends, Path

from dependencies import AuthDep, FeedSubscriptionServiceDep
from filters import FeedFilter
from lib.ext.fastapi import (
    Controller,
    IBaseResponse,
    IResponse,
    ORJSONResponse,
    before_action,
    delete,
    get,
    patch,
    post,
)
from lib.pagination import CursorPaginationMetadata, CursorParams, FilterDepends
from models import User
from schemas import FeedSubscriptionCreate, FeedSubscriptionOut, FeedSubscriptionUpdate
from settings import settings


class FeedSubscriptionController(Controller):
    """
    API Controller for managing feed subscription API endpoints.
    """

    prefix = f"{settings.API_V1_STR}/subscriptions"

    tags = ["Feed Subscriptions"]

    @before_action
    def authenticate(self, user: AuthDep):
        """
        Dependency to ensure that the user is authenticated before accessing feed-related endpoints.
        """
        self.current_user = cast(User, user)

    @get(
        "",
        operation_id="list_subscribed_feeds",
        response_model=IResponse[list[FeedSubscriptionOut], CursorPaginationMetadata],
    )
    async def list_subscribed_feeds(
        self,
        cursor: Annotated[CursorParams, Depends()],
        filter: Annotated[FeedFilter, FilterDepends(FeedFilter)],
        service: FeedSubscriptionServiceDep,
    ) -> ORJSONResponse:
        """
        List the user's subscribed feeds with the folders they belong to
        """
        message, data, metadata = await service.list_subscribed_feeds(self.current_user.id, cursor, filter)
        return self.json(message=message, data=data, metadata=metadata)

    @post("", operation_id="subscribe_feed", response_model=IBaseResponse)
    async def subscribe_to_feeds(
        self,
        body: Annotated[
            FeedSubscriptionCreate,
            Body(..., description="The URL of the feeds to subscribe to."),
        ],
        service: FeedSubscriptionServiceDep,
    ) -> ORJSONResponse:
        """
        Subscribe to a new feed by providing its URL.

        The feed will be fetched in the background if not already present and added to the user's subscriptions.
        """

        message = await service.subscribe_to_feeds(self.current_user.id, body)
        return self.json(message=message)

    @patch(
        "/{subscription_id}",
        operation_id="update_subscription",
        response_model=IBaseResponse,
    )
    async def update_subscription(
        self,
        subscription_id: Annotated[UUID, Path(..., description="The ID of the subscription to update.")],
        body: Annotated[
            FeedSubscriptionUpdate,
            Body(..., description="The updated data for the subscription."),
        ],
        service: FeedSubscriptionServiceDep,
    ) -> ORJSONResponse:
        """
        Update an existing feed subscription by its ID.

        This can be used to change the feed URL or other subscription details.
        """

        message = await service.update_subscription(self.current_user.id, subscription_id, body)
        return self.json(message=message)

    @delete(
        "/{subscription_id}",
        operation_id="unsubscribe_from_feed",
        response_model=IBaseResponse,
    )
    async def unsubscribe_from_feed(
        self,
        subscription_id: Annotated[
            UUID,
            Path(..., description="The ID of the subscription to unsubscribe from."),
        ],
        service: FeedSubscriptionServiceDep,
    ) -> ORJSONResponse:
        """
        Unsubscribe from a feed by its subscription ID.

        **NOTE**: The feed will be removed from the user's subscriptions but will not be deleted from the system,
        as other users may be subscribed to it.
        """

        message = await service.unsubscribe_from_feed(self.current_user, subscription_id)
        return self.json(message=message)

    @get(
        "/refresh",
        operation_id="refresh_subscriptions",
        response_model=IBaseResponse,
        include_in_schema=False,
    )
    async def refresh_subscriptions(
        self,
        service: FeedSubscriptionServiceDep,
    ) -> ORJSONResponse:
        """
        Trigger a refresh of all of the user's feed subscriptions by fetching the latest articles for each subscribed feed.
        """

        message = await service.refresh_subscriptions(self.current_user)
        return self.json(message=message)
