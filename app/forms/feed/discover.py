from pydantic import AnyHttpUrl

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button, FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class DiscoverFeedForm(BaseForm):
    """
    Form for discovering feeds
    """

    url: AnyHttpUrl = FormField(
        "url",
        html_attrs={
            "placeholder": "forms.placeholders.url",
        },
    )

    form_config = FormConfigDict(
        swap="none",
        submit_url="/api/v1/feeds/discover",
        submit_method="POST",
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="modal",
                condition="response.data != null && response.data.length === 0",
                fallback={
                    "name": "toast",
                    "context": {
                        "type": "info",
                        "message": "forms.discover.no_feeds_found",
                        "position": "bottom-middle",
                        "duration": 8000,
                        "auto_close_form": True,
                        "auto_close_form_with_selector": "#discover-feed-form-cancel-btn",
                    },
                },
                context={
                    "heading_icon": "check_circle",
                    "heading_title": "{response.message}",
                    "heading_subtitle": "forms.discover.heading_subtitle",
                    "content_url": '/forms/subscribe_to_feed_form?_attrs_urls={"options": {response.data}}',
                    "auto_close_form": True,
                    "auto_close_form_with_selector": "#discover-feed-form-cancel-btn",
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
        cancel_target="#discover-feed-form-container",
        cancel_restore_html="""
        <button
            id="discover-feed-form-retrieve-btn"
            class="fb-sidebar-add-btn" hx-get="/forms/discover_feed_form"
            hx-target="#discover-feed-form-container"
            hx-swap="innerHTML"
            hx-trigger="click"
        >
            <i class="f7-icons">plus_circle</i> {{ _t('forms.discover.add_feed_btn') }}
        </button>
        """,
        encoding="application/json",
        inline_validation=False,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-w-full fb-flex fb-justify-between fb-items-center fb-gap-0",
                "id": "discover-feed-form-buttons",
            },
            buttons=[
                Button(
                    text_or_html="""
                    <span data-loading>
                        <svg fill="var(--s1)" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/><path d="M12,4a8,8,0,0,1,7.89,6.7A1.53,1.53,0,0,0,21.38,12h0a1.5,1.5,0,0,0,1.48-1.75,11,11,0,0,0-21.72,0A1.5,1.5,0,0,0,2.62,12h0a1.53,1.53,0,0,0,1.49-1.3A8,8,0,0,1,12,4Z"><animateTransform attributeName="transform" type="rotate" dur="0.75s" values="0 12 12;360 12 12" repeatCount="indefinite"/></path></svg>
                    </span>
                    <span class="fb-text-xxs fb-font-medium">{{ _t('forms.discover.submit_btn') }}</span>
                    """,
                    html_attrs={
                        "id": "discover-feed-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary fb-w-85 fb-flex fb-items-center fb-justify-center",
                        "htmx-attrs": [
                            "data-loading-disabled",
                            "data-loading-path='/api/v1/feeds/discover'",
                        ],
                    },
                ),
                Button(
                    text_or_html="{{ _t('forms.buttons.cancel') }}",
                    html_attrs={
                        "id": "discover-feed-form-cancel-btn",
                        "type": "button",
                        "class": "fb-btn fb-btn-secondary fb-text-xxs fb-text-muted fb-font-medium",
                        "onclick": "window.HTMLUtils.cancelForm(this)",
                    },
                ),
            ],
        ),
    )
