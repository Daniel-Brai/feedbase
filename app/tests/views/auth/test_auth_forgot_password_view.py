from bootstrap.assets import configure_asset_manager
from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms

configure_auth()

from controllers.views import AuthViewController
from dependencies.auth import get_current_user_safe
from lib.auth.router import get_auth_router
from lib.testing import TestViewCase


class TestAuthForgotPasswordView(TestViewCase):
    """
    Tests for the authentication forgot password view
    """

    view_class = AuthViewController

    def get_dependency_overrides(self) -> dict:
        return {get_current_user_safe: lambda: None}

    def get_build_options(self) -> dict[str, list[str] | None]:
        return {"only": ["forgot_password", "login"]}

    async def asyncSetUp(self) -> None:
        configure_asset_manager()
        configure_controllers()

        await super().asyncSetUp()

        self.app.include_router(get_auth_router(auth_dep=lambda: None))
        configure_forms(self.app)

    async def test_forgot_password_view_renders_forgot_password_form(self) -> None:
        self.visit("/auth/forgot-password")

        self.assert_ok()
        self.assert_selector("form#forgot_password_form")
        self.assert_selector("form#change_language_form")
        self.assert_selector('a[href="/auth/login"]')

    async def test_forgot_password_view_includes_change_language_form(self) -> None:
        self.visit("/auth/forgot-password")

        self.assert_ok()
        self.assert_selector("form#change_language_form", count=1)

    async def test_forgot_password_view_includes_email_field_and_submit_button(
        self,
    ) -> None:
        self.visit("/auth/forgot-password")

        self.assert_ok()
        self.assert_selector('form#forgot_password_form input[name="email"]', count=1)
        self.assert_selector(
            'form#forgot_password_form button#forgot-password-form-submit-btn[type="submit"]',
            count=1,
        )

    async def test_forgot_password_form_submit_succeeds(self) -> None:
        self.visit("/auth/forgot-password")

        self.fill_in_form("form#forgot_password_form", 'input[name="email"]', "test@example.com")
        self.submit(form_selector="form#forgot_password_form")

        self.assert_ok()
        self.assert_contains("If that email is registered")

    async def test_click_login_link_navigates_to_login_page(self) -> None:
        self.visit("/auth/forgot-password")

        self.assert_ok()
        self.click('a[href="/auth/login"]')

        self.assert_ok()
        self.assert_selector("form#login_form")

    async def test_forgot_password_page_has_login_link(self) -> None:
        self.visit("/auth/forgot-password")

        self.assert_ok()
        self.assert_selector('a[href="/auth/login"]', count=1)
