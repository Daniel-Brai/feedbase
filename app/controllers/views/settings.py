from typing import cast

from fastapi import Request
from fastapi.responses import HTMLResponse

from constants import NOTIFICATION_CTX, settings_meta
from dependencies import AuthSafeDep
from forms import (
    ChangeEmailForm,
    ChangeLanguageForm,
    ChangePasswordForm,
    ExportOPMLForm,
    ImportOPMLForm,
    LogoutForm,
    RefreshFeedSubscriptionsForm,
    UpdateAvatarForm,
    UpdatePreferencesForm,
    UpdateProfileForm,
)
from lib.ext.fastapi import Controller, before_action, get
from models import User


class SettingsViewController(Controller):
    """
    Controller for handling requests to the settings view.
    """

    prefix = "/settings"

    include_in_schema = False

    @before_action
    def authenticate(self, user: AuthSafeDep):
        """
        Dependency to ensure that the user is authenticated before accessing the settings page.
        """
        if not user:
            return self.redirect("/auth/login")

        self.current_user = cast(User, user)

    @get("")
    async def settings(
        self,
        request: Request,
    ) -> HTMLResponse:
        return await self.render(
            "pages/settings.html",
            request=request,
            user=self.current_user,
            meta=settings_meta(),
            notifications=NOTIFICATION_CTX,
            navbar={
                "urls": {
                    "logout_form_url": LogoutForm.get_form_url(),
                    "settings_url": "/settings",
                    "update_avatar_form_url": UpdateAvatarForm.get_form_url(),
                    "update_preferences_form_url": UpdatePreferencesForm.get_form_url(),
                },
                "forms": {
                    "change_language_form": ChangeLanguageForm.get_form_name(),
                    "refresh_feeds_form": RefreshFeedSubscriptionsForm.get_form_name(),
                },
                "current_path": request.url.path,
            },
            sidebar={
                "account_url": "/settings/account",
                "opml_url": "/settings/opml",
                "active_page": "account",
                "forms": {
                    "update_profile_form": UpdateProfileForm.from_user(self.current_user),
                    "update_preferences_form": UpdatePreferencesForm.from_user(self.current_user),
                    "change_password_form": ChangePasswordForm.get_form_name(),
                    "change_email_form": ChangeEmailForm.from_user(self.current_user),
                    "export_opml_form": ExportOPMLForm.get_form_name(),
                    "import_opml_form": ImportOPMLForm.get_form_name(),
                },
            },
        )
