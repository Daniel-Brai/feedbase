from bootstrap.assets import configure_asset_manager
from bootstrap.auth import configure_auth
from bootstrap.controllers import configure_controllers
from bootstrap.form import configure_forms

configure_auth()

from controllers.views import AuthViewController
from dependencies.auth import get_current_user_safe
from lib.testing import TestViewCase


class TestAuthLoginView(TestViewCase):
    """
    Tests for the authentication login view
    """

    view_class = AuthViewController

    def get_dependency_overrides(self) -> dict:
        return {get_current_user_safe: lambda: None}

    def get_build_options(self) -> dict[str, list[str] | None]:
        return {"only": ["login"]}

    async def asyncSetUp(self) -> None:
        configure_asset_manager()
        configure_controllers()

        await super().asyncSetUp()

        configure_forms(self.app)

    async def test_login_view_renders_login_form_for_guest(self) -> None:
        self.visit("/auth/login")

        self.assert_ok()
        self.assert_selector("form#login_form")
        self.assert_selector("form#change_language_form")
        self.assert_selector('a[href="/auth/forgot-password"]')

    async def test_login_view_includes_change_language_form(self) -> None:
        self.visit("/auth/login")

        self.assert_ok()
        self.assert_selector("form#change_language_form", count=1)

    async def test_login_view_includes_login_fields_and_submit_button(self) -> None:
        self.visit("/auth/login")

        self.assert_ok()
        self.assert_selector('form#login_form input[name="email"]', count=1)
        self.assert_selector('form#login_form input[name="password"]', count=1)
        self.assert_selector('form#login_form button[type="submit"]', count=1)

    async def test_login_view_uses_htmx_post_to_auth_login_endpoint(self) -> None:
        self.visit("/auth/login")

        self.assert_ok()
        self.assert_selector('form#login_form[hx-post="/api/v1/auth/login"]')

    async def test_login_view_uses_correct_input_types_and_submit_button_id(
        self,
    ) -> None:
        self.visit("/auth/login")

        self.assert_ok()
        self.assert_selector('form#login_form input[name="email"][type="email"]', count=1)
        self.assert_selector('form#login_form input[name="password"][type="password"]', count=1)
        self.assert_selector('form#login_form button#login-form-submit-btn[type="submit"]', count=1)

    async def test_authenticated_user_is_redirected_to_home(self) -> None:
        self.override_dependency(get_current_user_safe, lambda: object())
        self.visit("/auth/login", follow_redirects=False)

        self.assert_found()
        assert self.browser.response is not None
        assert self.browser.response.headers["location"] == "/"
        assert self.browser.response.headers["HX-Location"] == "/"
