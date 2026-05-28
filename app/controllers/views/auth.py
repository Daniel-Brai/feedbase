from typing import Annotated

from fastapi import Path, Request
from fastapi.responses import HTMLResponse

from constants import NOTIFICATION_CTX, forgot_password_meta, login_meta, reset_password_meta, verify_email_meta
from dependencies import AuthSafeDep
from forms import ChangeLanguageForm, ForgotPasswordForm, LoginForm, ResetPasswordForm, VerifyEmailForm
from lib.ext.fastapi import Controller, before_action, get


class AuthViewController(Controller):
    """
    Controller for handling authentication-related views
    """

    prefix = "/auth"

    include_in_schema = False

    @before_action
    def redirect_if_authenticated(self, user: AuthSafeDep):
        """
        Dependency to redirect the user to the home page if they are already authenticated.
        """
        if user is not None:
            return self.redirect("/", headers={"HX-Location": "/"})

        return

    @get("/login")
    async def login(self, request: Request) -> HTMLResponse:
        return await self.render(
            "pages/auth/login.html",
            request=request,
            meta=login_meta(),
            notifications=NOTIFICATION_CTX,
            login_form=LoginForm.get_form_name(),
            change_language_form=ChangeLanguageForm.get_form_name(),
            forgot_password_link="/auth/forgot-password",
        )

    @get("/forgot-password")
    async def forgot_password(self, request: Request) -> HTMLResponse:
        return await self.render(
            "pages/auth/forgot_password.html",
            request=request,
            meta=forgot_password_meta(),
            notifications=NOTIFICATION_CTX,
            forgot_password_form=ForgotPasswordForm.get_form_name(),
            change_language_form=ChangeLanguageForm.get_form_name(),
            login_link="/auth/login",
        )

    @get("/reset-password/{token}")
    async def reset_password(
        self,
        request: Request,
        token: Annotated[
            str,
            Path(..., description="The password reset token sent to the user's email"),
        ],
    ) -> HTMLResponse:
        return await self.render(
            "pages/auth/reset_password.html",
            request=request,
            meta=reset_password_meta(),
            notifications=NOTIFICATION_CTX,
            reset_password_form=ResetPasswordForm.get_form_name(),
            change_language_form=ChangeLanguageForm.get_form_name(),
            token=token,
        )

    @get("/verify-email/{token}")
    async def verify_email(
        self,
        request: Request,
        token: Annotated[
            str,
            Path(..., description="The email verification token sent to the user's email"),
        ],
    ) -> HTMLResponse:
        return await self.render(
            "pages/auth/verify_email.html",
            request=request,
            meta=verify_email_meta(),
            notifications=NOTIFICATION_CTX,
            verify_email_form=VerifyEmailForm.get_form_name(),
            token=token,
        )
