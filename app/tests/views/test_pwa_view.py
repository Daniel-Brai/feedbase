from bootstrap.assets import configure_asset_manager
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms
from controllers.views import PWAViewController
from lib.testing import TestViewCase


class TestPWAView(TestViewCase):

    view_class = PWAViewController

    async def asyncSetUp(self) -> None:
        configure_asset_manager()

        configure_controllers()

        await super().asyncSetUp()

        configure_forms(self.app)

    async def test_offline_view_renders_offline_shell(self) -> None:
        self.visit("/offline")

        self.assert_ok()
        self.assert_selector("div#offline")
        self.assert_selector("button.fb-offline-btn")
        self.assert_selector("div#offline-empty-title")
        self.assert_selector("div#offline-empty-hint")

    async def test_service_worker_route_serves_javascript(self) -> None:
        self.browser.get("/sw.js")

        self.browser.assert_status(200)
        assert self.browser.response is not None
        assert "application/javascript" in self.browser.response.headers["content-type"]
