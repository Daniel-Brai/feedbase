from datetime import UTC, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from lib.ext.fastapi import Service, ServiceError
from models import User
from repositories import UserRepository
from schemas import UserAvatarOut, UserAvatarUpdate, UserOut, UserPreferencesUpdate, UserProfileUpdate


class UserService(Service):
    """
    Service for managing user-related operation like profile updates
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)

        self.user_repo = UserRepository(db)

    async def update_profile(self, user: User, data: UserProfileUpdate) -> tuple[str, UserOut, None]:
        """
        Update the user's profile information.

        Args:
            user (User): The user whose profile is being updated.
            data (UserProfileUpdate): The new profile information to update.

        Returns:
            tuple[str, UserOut, None]: A message, the updated user profile, and None for metadata.

        Raises:
            ServiceError: If there was an error updating the user profile.
        """

        try:
            updated_user = await self.user_repo.update_with_obj(user, data.model_dump(exclude_unset=True))

            await self.user_repo.commit()
            await self.user_repo.refresh(updated_user)

            return (
                "Profile updated successfully.",
                UserOut.from_model(updated_user),
                None,
            )
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            raise ServiceError("Failed to update your profile. Please try again.") from e

    async def update_avatar(self, user: User, data: UserAvatarUpdate) -> tuple[str, UserAvatarOut, None]:
        """
        Update the user's avatar.

        Args:
            user (User): The user whose avatar is being updated.
            data (UserAvatarUpdate): The new avatar information to update.

        Returns:
            tuple[str, UserAvatarOut, None]: A message, the updated avatar schema, and None for metadata.

        Raises:
            ServiceError: If there was an error updating the user avatar.
        """

        try:
            if user.avatar and user.avatar.attached:
                user.avatar.purge()

            user.avatar = data.to_attachment  # type: ignore

            updated_user = await self.user_repo.update_with_obj(user, {"updated_at": datetime.now(UTC)})

            await self.user_repo.commit()
            await self.user_repo.refresh(updated_user)

            return "Avatar updated successfully.", UserAvatarOut.from_model(updated_user), None

        except Exception as e:
            self.logger.error(f"Error updating user avatar: {e}")
            raise ServiceError("Failed to update your avatar. Please try again!") from e

    async def update_preferences(self, user: User, data: UserPreferencesUpdate) -> tuple[str, UserOut, None]:
        """
        Update the user's preferences.

        Args:
            user (User): The user whose preferences are being updated.
            data (UserPreferencesUpdate): The new preferences to update.

        Returns:
            tuple[str, UserOut, None]: A message, the updated user schema, and None for metadata.

        Raises:
            ServiceError: If there was an error updating the user preferences.
        """

        try:
            prefs = (
                user.preferences.copy()
                if user.preferences
                else {
                    "digest_frequency": None,
                    "digest_hour": 0,
                    "allow_push_notifications": False,
                    "mark_article_as_unread_if_updated": False,
                    "last_digest_sent": None,
                }
            )

            update_data = data.model_dump(exclude_unset=True)

            prefs.update(update_data)

            updated_user = await self.user_repo.update_with_obj(user, {"preferences": prefs})

            await self.user_repo.commit()
            await self.user_repo.refresh(updated_user)

            return (
                "Preferences updated successfully.",
                UserOut.from_model(updated_user),
                None,
            )
        except Exception as e:
            self.logger.error(f"Error updating user preferences: {e}")
            raise ServiceError("Failed to update your preferences. Please try again.") from e
