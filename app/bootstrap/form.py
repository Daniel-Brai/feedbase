from fastapi import FastAPI

from lib.forms import configure_forms as _configure_forms


def configure_forms(app: FastAPI):
    """
    Configure forms for the application
    """

    from bootstrap.templates import template_engine

    return _configure_forms(
        app=app,
        template_engine=template_engine,
        components={
            "avatar": "components/form/inputs/avatar.html",
            "checkbox": "components/form/inputs/checkbox.html",
            "email": "components/form/inputs/email.html",
            "hidden": "components/form/inputs/hidden.html",
            "file": "components/form/inputs/file.html",
            "multiselect": "components/form/inputs/multiselect.html",
            "number": "components/form/inputs/number.html",
            "password": "components/form/inputs/password.html",
            "search": "components/form/inputs/search.html",
            "select": "components/form/inputs/select.html",
            "text": "components/form/inputs/text.html",
            "textarea": "components/form/inputs/textarea.html",
            "toggle": "components/form/inputs/toggle.html",
            "url": "components/form/inputs/url.html",
            "language_switcher": "components/form/inputs/language_switcher.html",
        },
        modules=[
            "forms.user",
            "forms.auth",
            "forms.feed",
            "forms.feed_subscription",
            "forms.folder",
            "forms.i18n",
            "forms.opml",
        ],
        route_prefix="/forms",
        use_i18n=True,
    )
