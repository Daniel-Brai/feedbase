from typing import Annotated, cast
from uuid import UUID

from fastapi import Body, Path

from dependencies import AuthDep, FolderServiceDep
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
from models import User
from schemas import FolderCreate, FolderRead, FolderUpdate
from settings import settings


class FolderController(Controller):
    """
    API Controller for managing folder-related API endpoints.
    """

    prefix = f"{settings.API_V1_STR}/folders"

    @before_action
    def authenticate(self, user: AuthDep):
        """
        Dependency to ensure that the user is authenticated before accessing folder-related endpoints.
        """
        self.current_user = cast(User, user)

    @get(
        "",
        operation_id="list_folders",
        response_model=IResponse[list[FolderRead], None],
    )
    async def list_folders(
        self,
        service: FolderServiceDep,
    ) -> ORJSONResponse:
        """
        Retrieve a list of folders created by the authenticated user
        """

        message, data, metadata = await service.list_folders(self.current_user.id)
        return self.json(message=message, data=data, metadata=metadata)

    @post(
        "",
        operation_id="create_folder",
        response_model=IBaseResponse,
    )
    async def create_folder(
        self,
        body: Annotated[FolderCreate, Body(..., description="The details of the folder to create")],
        service: FolderServiceDep,
    ) -> ORJSONResponse:
        """
        Create a new folder for organizing feeds.
        """

        message = await service.create_folder(self.current_user, body)
        return self.json(message=message)

    @patch(
        "/{folder_id}",
        operation_id="update_folder",
        response_model=IBaseResponse,
    )
    async def update_folder(
        self,
        folder_id: Annotated[UUID, Path(..., description="The ID of the folder to update")],
        body: Annotated[FolderUpdate, Body(..., description="The updated details of the folder")],
        service: FolderServiceDep,
    ) -> ORJSONResponse:
        """
        Update an existing folder's details, such as its name or the feeds it contains.
        """

        message = await service.update_folder(self.current_user, folder_id, body)
        return self.json(message=message)

    @delete(
        "/{folder_id}",
        operation_id="delete_folder",
        response_model=IBaseResponse,
    )
    async def delete_folder(
        self,
        folder_id: Annotated[UUID, Path(..., description="The ID of the folder to delete")],
        service: FolderServiceDep,
    ) -> ORJSONResponse:
        """
        Delete a folder.

        If feeds exists in that folder, they will updated to have no folder (i.e. become "Uncategorized").
        """

        message = await service.delete_folder(self.current_user, folder_id)
        return self.json(message=message)
