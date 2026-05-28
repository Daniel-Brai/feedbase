from lib.forms import BaseForm
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class LogoutForm(BaseForm):
    """
    Form for user log out
    """

    form_config = FormConfigDict(
        swap="none",
        submit_url="/api/v1/auth/logout",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="no-op",
                context=None,
                redirect_to="/auth/login",
                redirect_delay_secs=0,
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
        encoding="application/json",
        inline_validation=False,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-btn-container fb-w-full",
                "id": "logout-form-buttons",
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
                    <span style="display: inline-flex; align-items: center; gap: 0.5rem;">
                       <i class="f7-icons fb-text-red">arrow_right_square</i> <span class="fb-text-red">{{ _t('forms.logout.submit_btn') }}</span>
                    </span>
                    """,
                    html_attrs={
                        "id": "logout-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-ghost fb-text-red fb-justify-start fb-w-full",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/auth/logout'",
                        ],
                    },
                )
            ],
        ),
    )
