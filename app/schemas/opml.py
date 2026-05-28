from fastapi import File, UploadFile
from pydantic import BaseModel, Field, model_validator

from constants import OPML_FILE_ALLOWED_EXTENSIONS, OPML_FILE_MAX_SIZE, OPML_FILE_MIME_TYPES
from lib.validators import validate_file


class OPMLImportRequest(BaseModel):
    """
    Schema representing the request body for an OPML import operation

    Attributes:
        file (UploadFile): The OPML file to import. Must be a valid OPML XML file.
    """

    file: UploadFile = File(..., description="The OPML file to import. Must be a valid OPML XML file.")

    @model_validator(mode="after")
    def validate_file(self) -> "OPMLImportRequest":
        """
        Validates the uploaded OPML file against defined constraints such as maximum size, allowed MIME types, and allowed file extensions.

        Raises:
            ValueError: If the file does not meet the validation criteria (e.g., exceeds max size, has disallowed MIME type or extension).

        Returns:
            OPMLImportRequest: The validated request object if the file is valid.
        """

        is_valid_file = validate_file(
            file=self.file,
            max_size=OPML_FILE_MAX_SIZE,
            allowed_content_types=list(OPML_FILE_MIME_TYPES),
            allowed_extensions=list(OPML_FILE_ALLOWED_EXTENSIONS),
            allow_empty=False,
        )

        if not is_valid_file["success"] and is_valid_file["errors"]:
            raise ValueError("Invalid OPML file: " + "; ".join(is_valid_file["errors"]))

        return self


class OPMLImportResultOut(BaseModel):
    """
    Schema representing the result of an OPML import operation

    Attributes:
        added (int): The number of new subscriptions created from the OPML import.
        skipped (int): The number of feeds in the OPML file that were already subscribed to
        failed (int): The number of feeds in the OPML file that failed to import due to errors.
        folders_created (int): The number of new folders created as part of the OPML import.
        errors (list[str]): A list of error messages encountered during the import process
    """

    added: int = Field(0, description="Number of new subscriptions created")
    skipped: int = Field(0, description="Number of already subscribed feeds skipped")
    failed: int = Field(0, description="Number of feeds that failed to import")
    folders_created: int = Field(0, description="Number of new folders created")
    errors: list[str] = Field(
        default_factory=list,
        description="List of error messages (limited to first 10)",
        max_length=10,
    )

    def model_dump(self, **kwargs) -> dict:
        data = super().model_dump(**kwargs)
        if "errors" in data and len(data["errors"]) > 10:
            data["errors"] = data["errors"][:10]

        return data
