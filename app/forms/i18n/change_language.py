from typing import Annotated

from pydantic import StringConstraints

from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormButtons, FormConfigDict
from lib.forms.types import Button


class ChangeLanguageForm(BaseForm):
    """
    Form for changing the user's preferred language
    """

    language: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)] = FormField(
        "language_switcher",
        html_attrs={
            "required": True,
            "options": [
                {
                    "value": "en",
                    "text": "EN",
                    "title": "English",
                },
                {
                    "value": "fr",
                    "text": "FR",
                    "title": "Français",
                },
            ],
        },
    )

    form_config = FormConfigDict(
        submit_url="/i18n/change-language",
        submit_method="POST",
        encoding="multipart/form-data",
        with_credentials=True,
        buttons=FormButtons(
            buttons_container_html_attrs={
                "class": "fb-hidden",
                "id": "change-language-form-buttons",
            },
            buttons=[
                Button(
                    text_or_html="""
                    <span>
                        {{ _t('forms.change_language.submit_btn') }}
                    </span>
                    """,
                    html_attrs={
                        "id": "change-language-form-submit-btn",
                        "type": "submit",
                        "class": "fb-btn fb-btn-primary fb-w-full fb-justify-center",
                    },
                ),
            ],
        ),
    )
