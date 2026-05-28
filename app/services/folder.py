from uuid import UUID

from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from lib.ext.fastapi import Service, ServiceError
from models import User
from notifiers import PaginationStreamNotification
from repositories import FeedSubscriptionRepository, FolderRepository
from schemas import FolderCreate, FolderRead, FolderUpdate


class FolderService(Service):
    """
    Service for managing folders.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)

        self.folder_repo = FolderRepository(db)
        self.feed_subscription_repo = FeedSubscriptionRepository(db)

    async def list_folders(self, user_id: int) -> tuple[str, list[FolderRead], None]:
        """
        List all folders for a user.

        Args:
            user_id (int): The ID of the user whose folders to list.

        Returns:
            tuple[str, list[FolderRead], None]: A tuple containing a message, a list of FolderRead objects representing the user's folders, and None for metadata (for consistency with other service methods).

        Raises:
            ServiceError: If there is an error retrieving the folders.
        """

        try:
            folders = await self.folder_repo.get_user_folders(user_id=user_id)
            data = [FolderRead.from_model(folder) for folder in folders]

            data.append(
                FolderRead(
                    id=None,
                    name="Uncategorized",
                    slug=None,
                )
            )

            return "Folders retrieved successfully", data, None
        except Exception as e:
            self.logger.error(f"Error listing folders for user {user_id}: {e}")
            raise ServiceError("Failed to retrieve folders. Please try again later.") from e

    async def create_folder(self, user: User, data: FolderCreate) -> str:
        """
        Create a folder

        Args:
            user (User): The user creating the folder.
            data (FolderCreate): The details of the folder to create.

        Returns:
            str: A message indicating the result of the folder creation operation.

        Raises:
            ServiceError: If a folder with the same name already exists or if there is an error during creation.
        """

        async with self.transaction():
            exists = await self.folder_repo.exists(user_id=user.id, name=data.name, parent_id=None)
            if exists:
                raise ServiceError(
                    f"A folder with this name '{data.name}' already exists.",
                    status_code=status.HTTP_409_CONFLICT,
                )

            await self.folder_repo.create({"user_id": user.id, "name": data.name})

        await PaginationStreamNotification(dom_id="subscriptions").deliver(user)

        return f"Folder '{data.name}' created successfully"

    async def update_folder(self, user: User, folder_id: UUID, data: FolderUpdate) -> str:
        """
        Update an existing folder's details, such as its name or the feeds it contains.

        Args:
            user (User): The user updating the folder.
            folder_id (UUID): The ID of the folder to update.
            data (FolderUpdate): The updated details of the folder.

        Returns:
            str: A message indicating the result of the folder update operation.

        Raises:
            ServiceError: If the folder is not found,
                            if a folder with the new name already exists, or if there is an error during the update.
        """

        async with self.transaction():
            folder = await self.folder_repo.get_by(id=folder_id, user_id=user.id)
            if not folder:
                raise ServiceError("Folder not found", status_code=status.HTTP_404_NOT_FOUND)

            if folder.name != data.name:
                exists = await self.folder_repo.exists(user_id=user.id, name=data.name, parent_id=folder.parent_id)
                if exists:
                    raise ServiceError(
                        f"A folder with this name '{data.name}' already exists.",
                        status_code=status.HTTP_409_CONFLICT,
                    )

                await self.folder_repo.update_with_obj(folder, {"name": data.name})

        await PaginationStreamNotification(dom_id="subscriptions").deliver(user)

        return "Folder updated successfully"

    async def delete_folder(self, user: User, folder_id: UUID) -> str:
        """
        Delete an existing folder.

        Args:
            user (User): The user deleting the folder.
            folder_id (UUID): The ID of the folder to delete.

        Returns:
            str: A message indicating the result of the folder deletion operation.

        Raises:
            ServiceError: If the folder is not found or if there is an error during deletion.
        """

        async with self.transaction():
            folder = await self.folder_repo.get_by(id=folder_id, user_id=user.id)
            if not folder:
                raise ServiceError("Folder not found", status_code=status.HTTP_404_NOT_FOUND)

            await self.feed_subscription_repo.clear_folder(user_id=user.id, folder_id=folder_id)

            await self.folder_repo.delete_with_obj(folder)

        await PaginationStreamNotification(dom_id="subscriptions").deliver(user)

        return "Folder deleted successfully"
