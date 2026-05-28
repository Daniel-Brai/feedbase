from typing import Literal

from pydantic import NonNegativeInt

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext
from models import User


class UpdatePreferencesForm(BaseForm):
    """
    Form for updating user preferences
    """

    digest_frequency: Literal["daily", "weekly"] | None = FormField(
        "select",
        html_attrs={
            "label": "forms.labels.digest_frequency",
            "options": [
                {"value": "daily", "text": "Daily"},
                {"value": "weekly", "text": "Weekly"},
            ],
            "options_placeholder": "forms.update_preferences.select_frequency",
            "required": False,
            "auto_submit_on_change": True,
        },
    )

    digest_hour: NonNegativeInt | None = FormField(
        "number",
        html_attrs={
            "label": "forms.labels.digest_hour",
            "min": 0,
            "max": 23,
            "required": False,
            "auto_submit_on_change": True,
        },
    )

    mark_article_as_unread_if_updated: bool = FormField(
        "toggle",
        html_attrs={
            "label": "forms.labels.mark_unread",
            "required": False,
            "auto_submit_on_change": True,
        },
    )

    allow_push_notifications: bool = FormField(
        "toggle",
        html_attrs={
            "label": "forms.labels.allow_push_notifications",
            "required": False,
            "auto_submit_on_change": True,
        },
    )

    form_config = FormConfigDict(
        swap="none",
        submit_url="/api/v1/accounts/me/preferences",
        submit_method="PATCH",
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
                    "title": "forms.update_preferences.error_title",
                    "message": "{error.detail}",
                },
            ),
        ),
        with_credentials=True,
        inline_validation=False,
        encoding="application/json",
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-hidden",
                "id": "update-preferences-form-buttons",
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
                    <span>{{ _t('forms.buttons.save_changes') }}</span>
                    """,
                    html_attrs={
                        "id": "update-preferences-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/accounts/me/preferences'",
                        ],
                    },
                )
            ],
        ),
    )

    @classmethod
    def from_user(cls, user: User) -> "UpdatePreferencesForm":
        digest_frequency = user.preferences.get("digest_frequency", None)
        digest_hour = user.preferences.get("digest_hour", None)
        mark_article_as_unread_if_updated = user.preferences.get("mark_article_as_unread_if_updated", False)
        allow_push_notifications = user.preferences.get("allow_push_notifications", False)

        return cls(
            digest_frequency=digest_frequency,
            digest_hour=digest_hour or 0,
            mark_article_as_unread_if_updated=mark_article_as_unread_if_updated,
            allow_push_notifications=allow_push_notifications,
        )
