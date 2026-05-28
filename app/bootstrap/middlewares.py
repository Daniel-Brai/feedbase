import uuid

from fastapi import FastAPI


def _configure_lib_middlewares(app: FastAPI):
    """
    Configure middlewares.
    """

    from hooks import request_timing_after_request, request_timing_before_request, request_timing_on_error

    from bootstrap.i18n import i18n
    from constants import EXCLUDED_REQUEST_PATHS
    from enums import ThrottlerBackend
    from lib.ext.fastapi import (
        CorrelationIdMiddleware,
        ETagMiddleware,
        RequestTimingMiddleware,
        SecurityHeadersMiddleware,
    )
    from lib.logger import RequestLoggingMiddleware
    from lib.templates import ErrorPageMiddleware
    from lib.throttler import ThrottlerMiddleware, is_throttler_configured
    from settings import settings

    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
        generator=lambda: uuid.uuid4().hex,
    )
    app.add_middleware(
        ETagMiddleware,
        exclude_paths=EXCLUDED_REQUEST_PATHS,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        RequestTimingMiddleware,
        header_name="X-Process-Time",
        before_request=(request_timing_before_request if settings.PROMETHEUS_METRICS_ENABLED else None),
        after_request=(request_timing_after_request if settings.PROMETHEUS_METRICS_ENABLED else None),
        on_error=(request_timing_on_error if settings.PROMETHEUS_METRICS_ENABLED else None),
    )

    app.add_middleware(
        ErrorPageMiddleware,
        favicon_url=f"{settings.APP_STATIC_URL}/images/favicon.ico",
        translator=lambda key, **kwargs: i18n.get_translator()(key, **kwargs),
    )

    app.add_middleware(
        SecurityHeadersMiddleware,
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self' https:; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=()",
        },
    )

    if settings.USE_THROTTLER_BACKEND != ThrottlerBackend.NOOP and is_throttler_configured():
        app.add_middleware(
            ThrottlerMiddleware,
            exclude_paths=EXCLUDED_REQUEST_PATHS,
        )


def configure_middlewares(app: FastAPI):
    """
    Configure middlewares for the FastAPI application.

    """

    _configure_lib_middlewares(app)
