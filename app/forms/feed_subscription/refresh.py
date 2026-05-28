from lib.forms import BaseForm
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class RefreshFeedSubscriptionsForm(BaseForm):
    """
    Form for refreshing feed subscriptions
    """

    form_config = FormConfigDict(
        swap="none",
        submit_url="/api/v1/subscriptions/refresh",
        submit_method="GET",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "forms.refresh_feeds.success_msg",
                    "position": "bottom-middle",
                    "duration": 4000,
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
        with_credentials=True,
        encoding="application/json",
        buttons=FormButtons(
            buttons_container_html_attrs={
                "id": "refresh-feeds-form-buttons",
            },
            buttons=[
                Button(
                    text_or_html="""
                    <span data-loading>
                        <i class="f7-icons fb-animate-spin fb-text-lg fb-text-muted">arrow_2_circlepath</i>
                    </span>
                    <span>
                        <i class="f7-icons fb-text-lg fb-text-muted">arrow_clockwise</i>
                    </span>
                    """,
                    html_attrs={
                        "id": "refresh-feed-form-submit-btn",
                        "type": "submit",
                        "class": "fb-navbar-icon-btn",
                        "title": "forms.refresh_feeds.title",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/feeds/trigger_refresh'",
                        ],
                    },
                ),
            ],
        ),
    )
