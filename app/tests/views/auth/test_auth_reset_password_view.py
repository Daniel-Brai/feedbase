from bootstrap.assets import configure_asset_manager
from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms

configure_auth()

from controllers.views import AuthViewController
from dependencies.auth import get_current_user_safe
from lib.testing import TestViewCase


class TestAuthResetPasswordView(TestViewCase):
    """
    Tests for the authentication reset password view
    """

    view_class = AuthViewController

    def get_dependency_overrides(self) -> dict:
        return {get_current_user_safe: lambda: None}

    def get_build_options(self) -> dict[str, list[str] | None]:
        return {"only": ["reset_password"]}

    async def asyncSetUp(self) -> None:
        configure_asset_manager()
        configure_controllers()

        await super().asyncSetUp()

        configure_forms(self.app)

    async def test_reset_password_view_renders_reset_password_form(self) -> None:
        self.visit("/auth/reset-password/token123")

        self.assert_ok()
        self.assert_selector("form#reset_password_form")
        self.assert_selector("form#change_language_form")
        self.assert_selector('input[name="token"]', count=1)
        self.assert_selector('input[name="password"][type="password"]', count=1)
        self.assert_selector(
            'button#reset-password-form-submit-btn[type="submit"]',
            count=1,
        )

    async def test_reset_password_view_renders_hidden_token_value(self) -> None:
        self.visit("/auth/reset-password/token123")

        self.assert_ok()
        self.assert_selector(
            'form#reset_password_form input[name="token"][type="hidden"][value="token123"]',
            count=1,
        )

    async def test_reset_password_view_includes_change_language_form(self) -> None:
        self.visit("/auth/reset-password/token123")

        self.assert_ok()
        self.assert_selector("form#change_language_form", count=1)
