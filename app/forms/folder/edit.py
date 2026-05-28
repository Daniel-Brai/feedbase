from typing import Annotated

from pydantic import StringConstraints

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class EditFolderForm(BaseForm):
    """
    Form for editing folders
    """

    name: Annotated[str, StringConstraints(min_length=2, max_length=500, strip_whitespace=True)] = FormField(
        "text",
        html_attrs={
            "placeholder": "forms.placeholders.folder_name",
            "required": True,
            "minlength": 2,
            "maxlength": 500,
        },
    )

    form_config = FormConfigDict(
        swap="none",
        submit_url="/api/v1/folders/{folder_id}",
        submit_method="PATCH",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "forms.edit_folder.success_msg",
                    "position": "bottom-middle",
                    "duration": 8000,
                    "auto_close_modal": True,
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
        inline_validation=True,
        inline_validation_threshold_seconds=15,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-btn-container fb-mt-4",
                "id": "edit-folder-form-buttons",
            },
            buttons=[
                Button(
                    text_or_html="{{ _t('forms.buttons.cancel') }}",
                    html_attrs={
                        "id": "edit-folder-form-cancel-btn",
                        "type": "button",
                        "class": "fb-btn fb-btn-secondary",
                        "onclick": "window.HTMLUtils.cancelModalForm(this)",
                    },
                ),
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
                    <span>{{ _t('forms.buttons.save') }}</span>
                    """,
                    html_attrs={
                        "id": "edit-folder-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary",
                        "htmx-attrs": [
                            "data-loading-disabled",
                        ],
                    },
                ),
            ],
        ),
    )
