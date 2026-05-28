from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import File, UploadFile
from pydantic import BaseModel, BeforeValidator, EmailStr, Field, NonNegativeInt, StringConstraints, model_validator

from lib.validators import validate_bool, validate_file, validate_string
from models import User


class UserOut(BaseModel):
    """
    Schema for a user response.

    Attributes:
        email (str): The email address of the user.
        name (str | None): The display name of the user, which can be null if
                            the user has not set a name.
        bio (str | None): A short biography of the user, which can be null if
                            the user has not set a bio.
        preferences (dict[str, Any]): A dictionary containing the user's preferences.
        avatar_url (str | None): The URL of the user's avatar image, which can be
                                null if the user has not set an avatar or if the avatar has been purged.
        is_active (bool): A boolean indicating whether the user's account is active.
        roles (list[str]): A list of roles assigned to the user.
        created_at (datetime): The datetime when the user account was created.
        updated_at (datetime | None): The datetime when the user account was last updated, which
    """

    email: str | EmailStr
    name: str
    bio: str | None
    preferences: dict[str, Any]
    avatar_url: str | None = None
    is_active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def from_model(cls, user: User) -> "UserOut":
        """
        Create a `UserOut` schema instance from a `User` model instance.
        """

        avatar_url = user.avatar.url if user.avatar and user.avatar.attached else None  # type: ignore[union-attr]
        return cls(
            email=user.email,
            name=user.name,
            bio=user.bio,
            preferences=user.preferences,
            avatar_url=avatar_url,
            is_active=user.is_active,
            roles=user.roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class UserPreferencesUpdate(BaseModel):
    """
    Schema for user profile preferences, including validation constraints and descriptions for API documentation.

    Attributes:
        digest_frequency (Literal["daily", "weekly"] | None): The frequency of article digests (daily or weekly).
        digest_hour (NonNegativeInt | None): The hour of the day (0-23) when the digest should be sent.
        mark_article_as_unread_if_updated (bool): Whether to mark articles as unread if they are updated after the user has read them.
        allow_push_notifications (bool): Whether to allow push notifications for new articles and updates.
    """

    digest_frequency: Annotated[
        Literal["daily", "weekly"] | None,
        BeforeValidator(validate_string()),
    ] = Field(
        None,
        description="The frequency of article digests. Can be 'daily' or 'weekly'.",
    )
    digest_hour: Annotated[NonNegativeInt | None, BeforeValidator(validate_string())] = Field(
        None,
        ge=0,
        le=23,
        description="The hour of the day (0-23) when the digest should be sent",
    )

    mark_article_as_unread_if_updated: Annotated[bool, BeforeValidator(validate_bool())] = Field(
        False,
        description="Whether to mark articles as unread if they are updated after the user has read them",
    )

    allow_push_notifications: Annotated[bool, BeforeValidator(validate_bool())] = Field(
        False,
        description="Whether to allow push notifications for new articles and updates",
    )


class UserProfileUpdate(BaseModel):
    """
    Schema for updating user profile information, including validation constraints and descriptions for API documentation.

    Attributes:
        name (str | None): The display name of the user, with a maximum length of 1000 characters.
        username (str | None): The unique username for the user, with a maximum length of 500 characters.
        bio (str | None): A short biography of the user, with a maximum length of 5000 characters.
    """

    name: Annotated[str, StringConstraints(max_length=1000, strip_whitespace=True)] | None = Field(
        None,
        description="The display name of the user, with a maximum length of 1000 characters.",
    )
    bio: Annotated[str, StringConstraints(max_length=5000, strip_whitespace=True)] | None = Field(
        None, description="The user's biography"
    )

    @model_validator(mode="after")
    def validate_profile(self):
        if self.name is None and self.bio is None:
            raise ValueError("At least one profile field must be provided")

        return self


class UserAvatarUpdate(BaseModel):
    """
    Schema for updating user avatar, which includes an optional file upload field for the avatar image.

    Attributes:
        avatar (UploadFile | None): The user's avatar image file, which must be a valid image format (e.g., JPEG, PNG) and not exceed 5 MB in size.
    """

    avatar: Annotated[UploadFile, File(..., description="The user's avatar image file.")]

    @model_validator(mode="after")
    def validate_avatar_file(self):
        if self.avatar is not None:
            result = validate_file(
                file=self.avatar,
                max_size=20 * 1024 * 1024,  # 20 MB
                allowed_content_types=["image/jpeg", "image/png", "image/webp"],
                allowed_extensions=[".jpg", ".jpeg", ".png", ".webp"],
                allow_empty=False,
            )

            if not result["success"] and result["errors"]:
                errors = "; ".join(result["errors"])
                raise ValueError(f"Invalid avatar file: {errors}")

        return self

    @property
    def to_attachment(self):
        """
        Converts the uploaded avatar file into a format suitable for attachment to the user's profile.

        Returns a tuple containing the filename, file object, and content type if the avatar is provided, or None if no avatar is uploaded.
        """

        if self.avatar is None:
            return None

        return (self.avatar.filename, self.avatar.file, self.avatar.content_type)


class UserAvatarOut(BaseModel):
    """
    Schema for representing the user's avatar in API responses, including the URL to the avatar image.

    Attributes:
        url (str | None, None): The URL where the user's avatar image can be accessed.
                            This field is optional and may be null if the user has not set an avatar or if the avatar has been purged
    """

    url: str | None = Field(None, description="The URL of the user's avatar image")

    @classmethod
    def from_model(cls, user: User) -> "UserAvatarOut":
        """
        Create a `UserAvatarOut` schema instance from a `User` model instance.
        """

        avatar_url = user.avatar.url if user.avatar and user.avatar.attached else None
        return cls(url=avatar_url)
