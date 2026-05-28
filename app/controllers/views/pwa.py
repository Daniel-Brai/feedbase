from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse

from constants import NOTIFICATION_CTX, offline_meta
from forms import ChangeLanguageForm
from lib.ext.fastapi import Controller, get
from settings import settings


class PWAViewController(Controller):
    """
    Controller for PWA related views.
    """

    include_in_schema = False

    @get("/offline")
    async def offline(self, request: Request) -> HTMLResponse:
        """
        Serve the offline page for the PWA when the user is not connected to the internet.
        """

        return await self.render(
            "pages/pwa/offline.html",
            request=request,
            meta=offline_meta(),
            notifications=NOTIFICATION_CTX,
            forms={
                "change_language_form": ChangeLanguageForm.get_form_name(),
            },
        )

    @get(
        "/sw.js",
        response_class=FileResponse,
    )
    async def service_worker(self) -> FileResponse:
        """
        Serve the service worker JavaScript file for the PWA.
        """

        sw_path = Path(settings.APP_ASSETS_DIR) / "pwa" / "sw.js"

        return FileResponse(
            sw_path,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )
