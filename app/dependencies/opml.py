from typing import Annotated

from fastapi import Depends

from services import OPMLExporterService, OPMLImporterService

from .database import AsyncDBSessionDep


def get_opml_export_service(db: AsyncDBSessionDep) -> OPMLExporterService:
    """
    Dependency provider for `OPMLExportService`.
    """

    return OPMLExporterService(db)


def get_opml_import_service(db: AsyncDBSessionDep) -> OPMLImporterService:
    """
    Dependency provider for `OPMLImportService`.
    """

    return OPMLImporterService(db)


OPMLExportServiceDep = Annotated[OPMLExporterService, Depends(get_opml_export_service)]
OPMLImportServiceDep = Annotated[OPMLImporterService, Depends(get_opml_import_service)]
