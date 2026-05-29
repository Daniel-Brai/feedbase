from fastapi import FastAPI

from lib.monitoring.prometheus import PrometheusMetricsConfig, configure_prometheus
from lib.monitoring.sentry import configure_sentry
from settings import settings


def configure_monitoring(app: FastAPI) -> None:
    """
    Configure monitoring for the application, including Sentry for error tracking and Prometheus for metrics.
    """

    if settings.APP_MONITORING_ENABLED:
        if settings.SENTRY_DSN:

            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration

            configure_sentry(
                dsn=settings.SENTRY_DSN,
                environment=settings.APP_ENVIRONMENT.value,
                send_default_pii=False,
                integrations=[
                    CeleryIntegration(),
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                    StarletteIntegration(),
                ],
            )

        if settings.PROMETHEUS_METRICS_ENABLED:

            from constants import (
                JOBS_DURATION,
                JOBS_PROCESSED,
                REQUEST_ERRORS,
                REQUESTS_IN_PROGRESS,
                TEMPLATE_RENDER_DURATION,
            )

            configure_prometheus(
                app,
                config=PrometheusMetricsConfig(
                    app_name=settings.APP_NAME.lower(),
                    metrics_endpoint=settings.PROMETHEUS_METRICS_URL,
                    excluded_handlers=["/health", "/ready", "/metrics"],
                    include_app_name_label=True,
                    custom_metrics=[
                        JOBS_DURATION,
                        JOBS_PROCESSED,
                        REQUEST_ERRORS,
                        REQUESTS_IN_PROGRESS,
                        TEMPLATE_RENDER_DURATION,
                    ],
                ),
            )
