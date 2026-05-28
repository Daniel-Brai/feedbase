from typing import Any

from bootstrap.assets import configure_asset_manager
from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms

configure_auth()

from controllers.views import SettingsViewController
from lib.testing import TestViewCase
from settings import settings
from tests.utils import create_verified_user, mount_auth_routes


class TestSettingsView(TestViewCase):

    view_class = SettingsViewController

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
            bio="Test bio",
            preferences={
                "digest_frequency": "weekly",
                "digest_hour": 13,
                "mark_article_as_unread_if_updated": True,
                "allow_push_notifications": True,
            },
        )

        response = self.browser.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": self.user.email, "password": password},
        )
        assert response.status_code == 200, response.text

    async def test_settings_view_redirects_guest_to_login(self) -> None:
        self.visit("/settings", follow_redirects=False)

        self.assert_found()

        assert self.browser.response is not None
        assert self.browser.response.headers["location"] == "/auth/login"

    async def test_settings_view_renders_settings_for_authenticated_user(self) -> None:
        await self.authenticate_user()

        self.visit("/settings")

        self.assert_ok()
        self.assert_selector("div#settings")
        self.assert_selector("form#update_profile_form")
        self.assert_selector("form#change_email_form")
        self.assert_selector("form#update_preferences_form")
        self.assert_selector("form#export_opml_form")
        self.assert_selector('input[name="email"][type="email"]')
        self.assert_selector("button#update-profile-form-submit-btn")
        self.assert_contains(self.user.name)
        self.assert_contains(self.user.bio)
        self.assert_contains(self.user.email)
        self.assert_selector('a[href="/"]')
