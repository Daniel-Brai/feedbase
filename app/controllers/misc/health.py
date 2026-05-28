from fastapi import Response

from dependencies import HealthServiceDep
from lib.ext.fastapi import Controller, get


class HealthController(Controller):
    """
    Health Controller.
    """

    include_in_schema = False

    @get(
        "/health",
        operation_id="health_check",
        summary="Health Check Endpoint",
    )
    async def health_check(self, service: HealthServiceDep) -> Response:
        """
        Health check endpoint.

        This endpoint can be used by load balancers or monitoring tools to check if the application is healthy and responsive.
        """

        result = service.health_check()

        return self.raw(result, media_type="text/plain")

    @get(
        "/ready",
        operation_id="readiness_check",
        summary="Readiness Check Endpoint",
    )
    async def readiness_check(self, service: HealthServiceDep) -> Response:
        """
        Readiness check endpoint.

        This endpoint can be used by load balancers or monitoring tools to check if the application is ready to receive traffic. This can be used to prevent traffic from being sent to the application before it has finished starting up or initializing.
        """

        result = service.readiness_check()

        return self.raw(result, media_type="application/json")
