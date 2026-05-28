from pydantic import EmailStr

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext
from models import User


class ChangeEmailForm(BaseForm):
    """
    Form for changing user email address
    """

    email: EmailStr = FormField(
        "email",
        html_attrs={
            "label": "forms.labels.email",
            "placeholder": "forms.placeholders.new_email",
            "required": True,
            "data-enable-on-changed-value": "true",
        },
    )

    form_config = FormConfigDict(
        submit_url="/api/v1/auth/me/change-email",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "{response.message}",
                    "position": "bottom-middle",
                    "duration": 8000,
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
        with_credentials=True,
        inline_validation=True,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-mt-4",
                "id": "change-email-form-buttons",
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
                    <span>{{ _t('forms.change_email.submit_btn') }}</span>
                    """,
                    html_attrs={
                        "id": "change-email-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary",
                        "disabled": True,
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/auth/me/change-email'",
                        ],
                    },
                )
            ],
        ),
    )

    @classmethod
    def from_user(cls, user: User) -> "ChangeEmailForm":
        """
        Create a ChangeEmailForm instance pre-filled with the user's current email
        """
        return cls(
            email=user.email,
        )
