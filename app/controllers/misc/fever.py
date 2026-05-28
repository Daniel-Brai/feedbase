from typing import Annotated

from fastapi import Depends, Response

from dependencies import FeverServiceDep
from lib.ext.fastapi import Controller, post
from schemas import FeverForm, FeverQuery, FeverResponseOut


class FeverController(Controller):
    """
    Fever Controller.

    This controller implements the Fever API, allowing third-party RSS reader
    clients to sync with Feedbase.
    """

    prefix = "/fever"

    tags = ["Fever API"]

    @post(
        "",
        operation_id="fever_api",
        summary="Handle Fever API Request",
        response_model=FeverResponseOut,
    )
    async def handle_request(
        self,
        q: Annotated[FeverQuery, Depends()],
        f: Annotated[FeverForm, Depends()],
        service: FeverServiceDep,
    ) -> Response:
        """
        Handle requests to Feedbase using the [Fever Specification](https://web.archive.org/web/20230616124016/https://feedafever.com/api).

        It allows the user to sync data such as feeds, items,
        and so on with Feedbase using third-party clients that support the Fever API, such as Reeder or ReadKit.
        """

        result = await service.handle_request(q, f)
        response = self.raw(result.model_dump_json(exclude_none=True), media_type="application/json")

        return await service.post_process_response(q, f, result, response)
