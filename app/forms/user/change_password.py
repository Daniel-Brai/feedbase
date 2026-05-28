from lib.auth.types import Password
from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class ChangePasswordForm(BaseForm):
    """
    Form for changing the user password
    """

    current_password: Password = FormField(
        "password",
        html_attrs={
            "label": "forms.labels.current_password",
            "placeholder": "forms.placeholders.password",
            "required": True,
            "autocomplete": "off",
            "min_length": 8,
            "max_length": 128,
            "include_numbers": True,
            "include_special_chars": True,
            "include_lowercase": True,
            "include_uppercase": True,
        },
    )

    new_password: Password = FormField(
        "password",
        html_attrs={
            "label": "forms.labels.new_password",
            "placeholder": "forms.placeholders.password",
            "required": True,
            "autocomplete": "off",
            "min_length": 8,
            "max_length": 128,
            "include_numbers": True,
            "include_special_chars": True,
            "include_lowercase": True,
            "include_uppercase": True,
        },
    )

    form_config = FormConfigDict(
        submit_url="/api/v1/auth/change-password",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "forms.change_password.success_msg",
                    "position": "bottom-middle",
                    "duration": 8000,
                },
            ),
            error=FormSubmissionErrorContext(
                name="alert",
                context={
                    "type": "error",
                    "title": "forms.change_password.error_title",
                    "message": "{error.detail}",
                },
            ),
        ),
        with_credentials=True,
        inline_validation=False,
        encoding="application/json",
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-container fb-mt-4",
                "id": "update-password-form-buttons",
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
                    <span> {{ _t('forms.change_password.submit_btn') }} </span>
                    """,
                    html_attrs={
                        "id": "update-password-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/auth/change-password'",
                        ],
                    },
                )
            ],
        ),
    )
