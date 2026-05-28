from typing import Annotated, cast

from fastapi import Depends, Response

from dependencies import AuthDep, OPMLExportServiceDep, OPMLImportServiceDep
from lib.ext.fastapi import Controller, IResponse, ORJSONResponse, before_action, post
from models import User
from schemas import OPMLImportRequest, OPMLImportResultOut


class OPMLController(Controller):
    """
    Controller for managing OPML-related endpoints.
    """

    prefix = "/opml"

    tags = ["OPML"]

    @before_action
    def authenticate(self, user: AuthDep):
        """
        Dependency to ensure that the user is authenticated before accessing OPML-related endpoints.
        """
        self.current_user = cast(User, user)

    @post(
        "/export",
        summary="Export OPML",
        description="Export the user's feeds in OPML format.",
        responses={200: {"content": {"text/x-opml": {}}}},
    )
    async def export_opml(self, service: OPMLExportServiceDep) -> Response:
        """
        Export the user's subscriptions as an OPML file.

        If the user has no subscriptions, an empty string is returned with a 204 No Content status.
        """

        result = await service.run(user_id=self.current_user.id)

        def generate_chunks():
            data = result.encode("utf-8")
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                yield data[i : i + chunk_size]

        return self.stream(
            content=generate_chunks(),
            media_type="text/x-opml",
            headers={"Content-Disposition": "attachment; filename=feedbase-subscriptions.opml"},
        )

    @post(
        "/import",
        summary="Import OPML",
        description="Import feeds from an OPML file.",
        response_model=IResponse[OPMLImportResultOut, None],
    )
    async def import_opml(
        self, body: Annotated[OPMLImportRequest, Depends()], service: OPMLImportServiceDep
    ) -> ORJSONResponse:
        """
        Import feeds from an uploaded OPML file.
        """

        contents = await body.file.read()

        result = await service.run(
            user_id=self.current_user.id,
            opml_content=contents,
        )

        return self.json(
            message="OPML import completed successfully",
            data=result,
        )
