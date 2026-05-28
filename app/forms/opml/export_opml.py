from lib.forms import BaseForm
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class ExportOPMLForm(BaseForm):
    """
    Form for exporting the user's subscriptions as an OPML file.
    """

    form_config = FormConfigDict(
        swap="none",
        submit_url="/opml/export",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="no-op",
                context=None,
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
        use_htmx=False,
        encoding="multipart/form-data",
        inline_validation=False,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-btn-container fb-w-full",
                "id": "export-opml-form-buttons",
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
                    <span class="fb-inline-flex fb-items-center fb-gap-1">
                        <i class="f7-icons fb-text-lg">download_circle</i>
                        <span>Export OPML</span>
                    </span>
                    """,
                    html_attrs={
                        "id": "export-opml-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/opml/export'",
                        ],
                    },
                )
            ],
        ),
    )
