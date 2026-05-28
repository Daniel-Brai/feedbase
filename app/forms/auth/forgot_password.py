from typing import Annotated

from pydantic import EmailStr, StringConstraints

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class ForgotPasswordForm(BaseForm):
    """
    Form for requesting a password reset
    """

    email: Annotated[EmailStr, StringConstraints(strip_whitespace=True, to_lower=True)] = FormField(
        "email",
        html_attrs={
            "label": "forms.forgot_password.email_label",
            "placeholder": "forms.forgot_password.email_placeholder",
            "required": True,
        },
    )

    form_config = FormConfigDict(
        submit_url="/api/v1/auth/forgot-password",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="alert",
                context={
                    "type": "success",
                    "title": "forms.forgot_password.success_title",
                    "message": "forms.forgot_password.success_msg",
                },
            ),
            error=FormSubmissionErrorContext(
                name="alert",
                context={
                    "type": "error",
                    "title": "forms.error",
                    "message": "{error.detail}",
                },
            ),
        ),
        encoding="application/json",
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-btn-container fb-mt-4 fb-w-full",
                "id": "forgot-password-form-buttons",
            },
            buttons=[
                Button(
                    text_or_html="""
                    <span data-loading>
                        <svg fill="var(--s1)" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/>
                            <path d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z">
                                <animateTransform attributeName="transform" type="rotate" dur="1s" repeatCount="indefinite" from="0 12 12" to="360 12 12"/>
                            </path>
                        </svg>
                    </span>
                    <span>
                        <i class="f7-icons">paperplane_fill</i> {{ _t('forms.forgot_password.submit_btn') }}
                    </span>
                    """,
                    html_attrs={
                        "id": "forgot-password-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary fb-w-full fb-justify-center",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/auth/forgot-password'",
                        ],
                    },
                )
            ],
        ),
    )
