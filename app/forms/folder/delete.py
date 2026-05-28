from lib.forms import BaseForm
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class DeleteFolderForm(BaseForm):
    """
    Form for editing folders
    """

    form_config = FormConfigDict(
        swap="none",
        submit_url="/api/v1/folders/{folder_id}",
        submit_method="DELETE",
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
                name="toast",
                context={"type": "error", "message": "{error.detail}", "position": "bottom-middle", "duration": 8000},
            ),
        ),
        encoding="application/json",
        inline_validation=False,
        with_credentials=True,
        buttons=FormButtons(
            buttons=[
                Button(
                    text_or_html="""
                    <i class="f7-icons">trash</i>
                    <span>{{ _t('sidebar.delete_folder') }}</span>
                    """,
                    html_attrs={
                        "id": "delete-folder-form-submit-btn",
                        "type": "submit",
                        "class": "fb-popover-option danger",
                        "htmx-attrs": ["data-loading-disabled"],
                    },
                ),
            ]
        ),
    )
