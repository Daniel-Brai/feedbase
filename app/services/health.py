import json

from lib.database.utils import ping_database
from lib.ext.fastapi import BaseService
from settings import settings


class HealthService(BaseService):
    """
    Service responsible for handling health checks and readiness checks.
    """

    def __init__(self) -> None:
        super().__init__()

    def health_check(self) -> str:
        """
        Performs a health check to determine if the service is healthy.

        Returns:
            str: A message indicating the health status.
        """

        return "OK"

    def readiness_check(self) -> str:
        """
        Performs a readiness check to determine if the service is ready to receive traffic.

        Returns:
            str: A JSON string indicating the readiness status and the status of dependent services.
        """

        result = {
            "status": "OK",
            "services": {
                "database": ("OK" if ping_database(str(settings.APP_SQLALCHEMY_DATABASE_SYNC_URI)) else "DEGRADED"),
            },
        }

        return json.dumps(result)
