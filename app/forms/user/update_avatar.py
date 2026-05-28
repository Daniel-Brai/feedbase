from fastapi import UploadFile

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class UpdateAvatarForm(BaseForm):
    """
    Form for updating user avatar
    """

    avatar: UploadFile = FormField(
        "avatar",
        html_attrs={
            "required": True,
            "accept": "image/*",
            "max_size": "10MB",
        },
    )

    form_config = FormConfigDict(
        submit_url="/api/v1/accounts/me/avatar",
        submit_method="PATCH",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "forms.update_avatar.success_msg",
                    "position": "bottom-middle",
                    "duration": 8000,
                },
            ),
            error=FormSubmissionErrorContext(
                name="toast",
                context={
                    "type": "error",
                    "message": "forms.update_avatar.error_msg",
                    "position": "bottom-middle",
                    "duration": 8000,
                },
            ),
        ),
        with_credentials=True,
        inline_validation=False,
        buttons=FormButtons(
            buttons_container_html_attrs={"class": "fb-hidden", "id": "update-avatar-form-buttons"},
            buttons=[
                Button(
                    text_or_html="{{ _t('forms.update_avatar.submit_btn') }}",
                    html_attrs={
                        "id": "update-avatar-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary",
                    },
                )
            ],
        ),
    )
