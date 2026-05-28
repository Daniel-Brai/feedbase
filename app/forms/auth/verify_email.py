from lib.forms import BaseForm
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class VerifyEmailForm(BaseForm):
    """
    Form for verifying a user's email address
    """

    form_config = FormConfigDict(
        swap="none",
        trigger="load",
        submit_url="/api/v1/auth/verify-email/{token}",
        submit_method="GET",
        submit_on_page_load=True,
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="alert",
                context={
                    "type": "success",
                    "title": "forms.verify_email.success_title",
                    "message": "forms.verify_email.success_msg",
                },
                redirect_to="/auth/login",
                redirect_delay_secs=5,
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
        inline_validation=False,
        buttons=FormButtons(
            buttons_container_html_attrs={"class": "fb-btn-container fb-mt-4", "id": "verify-email-form-buttons"},
            buttons=[
                Button(
                    text_or_html="{{ _t('forms.verify_email.submit_btn') }}",
                    html_attrs={
                        "id": "verify-email-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-hidden",
                    },
                )
            ],
        ),
    )
