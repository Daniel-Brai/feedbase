from typing import Annotated

from fastapi import File, UploadFile

from constants import OPML_FILE_MIME_TYPES
from lib.forms import BaseForm, FormField
from lib.forms.schemas import FormConfigDict
from lib.forms.types import FormSubmissionErrorContext, FormSubmissionSuccessContext, SubmitContext


class ImportOPMLForm(BaseForm):
    """
    Form for importing OPML files.
    """

    file: Annotated[UploadFile, File()] = FormField(
        "file",
        html_attrs={
            "accept": f".opml,{','.join(OPML_FILE_MIME_TYPES)}",
            "style": "drag_and_drop",
            "mode": "single",
            "auto_submit_on_select": True,
            "max_size": "20MB",
        },
    )

    form_config = FormConfigDict(
        swap="none",
        submit_url="/opml/import",
        submit_method="POST",
        encoding="multipart/form-data",
        inline_validation=False,
        submit_context=SubmitContext(
            success=FormSubmissionSuccessContext(
                name="toast",
                context={
                    "type": "success",
                    "message": "forms.opml.import_success",
                    "position": "bottom-middle",
                    "duration": 8000,
                },
            ),
            error=FormSubmissionErrorContext(
                name="toast",
                context={
                    "type": "error",
                    "message": "forms.opml.import_error",
                    "position": "bottom-middle",
                    "duration": 8000,
                },
            ),
        ),
    )
