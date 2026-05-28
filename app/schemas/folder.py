from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints


class FolderCreate(BaseModel):
    """
    Schema for creating a new folder.

    Attributes:
        name (str): The name of the folder.
    """

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=500)] = Field(
        ..., description="The name of the folder", examples=["Tech News"]
    )


class FolderUpdate(FolderCreate):
    """
    Schema for updating an existing folder.

    Attributes:
        name (str): The new name of the folder.
    """

    pass


class FolderRead(BaseModel):
    """
    Schema for reading folder information.

    Attributes:
        id (UUID): The unique identifier of the folder.
        name (str): The name of the folder.
        slug (str | None): The slug of the folder, used for URL-friendly identifiers.
    """

    id: UUID | None = Field(..., description="The unique identifier of the folder")
    name: str = Field(..., description="The name of the folder")
    slug: str | None = Field(None, description="The slug of the folder, used for URL-friendly identifiers")

    @classmethod
    def from_model(cls, folder):
        """
        Create a :class:`FolderRead` instance from a :class:`~models.Folder` model instance.
        """

        return cls(
            id=folder.id,
            name=folder.name,
            slug=folder.slug,
        )
