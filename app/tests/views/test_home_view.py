from typing import Any

from bootstrap.assets import configure_asset_manager
from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms

configure_auth()

from controllers.views import HomeViewController
from lib.testing import TestViewCase
from settings import settings
from tests.utils import create_verified_user, mount_auth_routes


class TestHomeView(TestViewCase):

    view_class = HomeViewController

    async def asyncSetUp(self) -> None:
        configure_asset_manager()

        configure_controllers()

        await super().asyncSetUp()

        configure_forms(self.app)

        mount_auth_routes(self.app)

        self.user: Any = None

    async def authenticate_user(self) -> None:
        self.user, password = await create_verified_user(
            name="Test User",
            bio="A test user",
            preferences={
                "digest_frequency": "daily",
                "digest_hour": 9,
                "mark_article_as_unread_if_updated": True,
                "allow_push_notifications": False,
            },
        )

        response = self.browser.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": self.user.email, "password": password},
        )
        assert response.status_code == 200, response.text

    async def test_home_view_redirects_guest_to_login(self) -> None:
        self.visit("/", follow_redirects=False)

        self.assert_found()

        assert self.browser.response is not None
        assert self.browser.response.headers["location"] == "/auth/login"

    async def test_home_view_renders_home_for_authenticated_user(self) -> None:
        await self.authenticate_user()

        self.visit("/")

        self.assert_ok()
        self.assert_selector("div#home")
        self.assert_selector("form#logout_form")
        self.assert_selector("div#discover-feed-form-container")
        self.assert_selector("div#add-folder-form-container")
        self.assert_selector('a[href="/settings"]')
        self.assert_contains(self.user.name)
