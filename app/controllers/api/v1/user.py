from typing import Annotated, cast

from fastapi import Body, Depends

from dependencies import AuthDep, UserServiceDep
from lib.ext.fastapi import Controller, IResponse, ORJSONResponse, before_action, patch
from models import User
from schemas import UserAvatarOut, UserAvatarUpdate, UserOut, UserPreferencesUpdate, UserProfileUpdate
from settings import settings


class UserController(Controller):
    """
    API Controller for managing user-related API endpoints.
    """

    prefix = f"{settings.API_V1_STR}/accounts"

    tags = ["Accounts"]

    @before_action
    def authenticate(self, user: AuthDep):
        """
        Dependency to ensure that the user is authenticated before accessing user-related endpoints.
        """
        self.current_user = cast(User, user)

    @patch(
        "/me",
        operation_id="update_profile",
        response_model=IResponse[UserOut, None],
    )
    async def update_profile(
        self,
        body: Annotated[
            UserProfileUpdate,
            Body(..., description="The updated user profile information."),
        ],
        service: UserServiceDep,
    ) -> ORJSONResponse:
        """
        Update the current user's information.
        """

        message, data, metadata = await service.update_profile(self.current_user, body)
        return self.json(message=message, data=data, metadata=metadata)

    @patch(
        "/me/avatar",
        operation_id="update_user_avatar",
        response_model=IResponse[UserAvatarOut, None],
    )
    async def update_avatar(
        self,
        body: Annotated[UserAvatarUpdate, Depends()],
        service: UserServiceDep,
    ) -> ORJSONResponse:
        """
        Update the current user's avatar.
        """

        message, data, metadata = await service.update_avatar(self.current_user, body)
        return self.json(message=message, data=data, metadata=metadata)

    @patch(
        "/me/preferences",
        operation_id="update_user_preferences",
        response_model=IResponse[UserOut, None],
    )
    async def update_preferences(
        self,
        body: Annotated[
            UserPreferencesUpdate,
            Body(..., description="The updated user preferences."),
        ],
        service: UserServiceDep,
    ) -> ORJSONResponse:
        """
        Update the current user's preferences.
        """

        message, data, metadata = await service.update_preferences(self.current_user, body)
        return self.json(message=message, data=data, metadata=metadata)
