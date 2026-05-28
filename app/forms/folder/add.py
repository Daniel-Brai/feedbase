from typing import Annotated

from pydantic import StringConstraints

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class AddFolderForm(BaseForm):
    """
    Form for adding folders
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
        css="fb-pb-2 fb-pl-2x fb-pr-2x",
        swap="none",
        submit_url="/api/v1/folders",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "forms.add_folder.success_msg",
                    "position": "bottom-middle",
                    "duration": 8000,
                    "auto_close_form": True,
                    "auto_close_form_with_selector": "#add-folder-form-cancel-btn",
                },
            ),
            error=FormSubmissionErrorContext(
                name="toast",
                context={
                    "type": "error",
                    "message": "{error.detail}",
                    "position": "bottom-middle",
                    "duration": 8000,
                },
            ),
        ),
        cancel_target="#add-folder-form-container",
        cancel_restore_html="""
        <div class="fb-sidebar-feeds-header">
        <p class="fb-sidebar-section">{{ _t('sidebar.feeds') }}</p>
        <button
            type="button"
            id="add-folder-form-retrieve-btn"
            hx-get="/forms/add_folder_form"
            hx-target="#add-folder-form-container"
            hx-swap="innerHTML"
            hx-trigger="click"
            class="fb-sidebar-add-folder-btn"
            title="{{ _t('sidebar.new_folder') }}"
        >
            <i class="f7-icons">folder_badge_plus</i>
        </button>
        </div>
        """,
        encoding="application/json",
        with_credentials=True,
        inline_validation=False,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-w-full fb-flex fb-justify-between fb-items-center fb-gap-0",
                "id": "add-folder-form-buttons",
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
                    <span>{{ _t('forms.add_folder.submit_btn') }}</span>
                    """,
                    html_attrs={
                        "id": "add-folder-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary fb-w-85 fb-flex fb-items-center fb-justify-center",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/folders'",
                        ],
                    },
                ),
                Button(
                    text_or_html="{{ _t('forms.buttons.cancel') }}",
                    html_attrs={
                        "id": "add-folder-form-cancel-btn",
                        "type": "button",
                        "class": "fb-btn fb-btn-secondary fb-text-xxs fb-text-muted fb-font-medium",
                        "onclick": "window.HTMLUtils.cancelForm(this)",
                    },
                ),
            ],
        ),
    )
