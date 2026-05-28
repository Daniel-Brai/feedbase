from bootstrap.assets import configure_asset_manager
from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms

configure_auth()

from controllers.views import AuthViewController
from dependencies.auth import get_current_user_safe
from lib.testing import TestViewCase


class TestAuthVerifyEmailView(TestViewCase):
    """
    Tests for the authentication verify email view
    """

    view_class = AuthViewController

    def get_dependency_overrides(self) -> dict:
        return {get_current_user_safe: lambda: None}

    def get_build_options(self) -> dict[str, list[str] | None]:
        return {"only": ["verify_email"]}

    async def asyncSetUp(self) -> None:
        configure_asset_manager()
        configure_controllers()

        await super().asyncSetUp()

        configure_forms(self.app)

    async def test_verify_email_view_renders_verify_email_form(self) -> None:
        self.visit("/auth/verify-email/test-token")

        self.assert_ok()
        self.assert_selector("form#verify_email_form")
        self.assert_selector(
            'button#verify-email-form-submit-btn[type="submit"]',
            count=1,
        )

    async def test_verify_email_view_uses_submit_on_page_load_with_token(self) -> None:
        self.visit("/auth/verify-email/test-token")

        self.assert_ok()
        self.assert_selector(
            'form#verify_email_form[hx-get="/api/v1/auth/verify-email/test-token"][hx-trigger="load"]',
            count=1,
        )
