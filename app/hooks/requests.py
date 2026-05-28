from constants import EXCLUDED_REQUEST_PATHS, REQUEST_ERRORS, REQUESTS_IN_PROGRESS
from lib.ext.fastapi import check_if_path_excluded


def request_timing_before_request(scope):
    method = scope.get("method", "")
    endpoint = scope.get("path", "")

    if check_if_path_excluded(EXCLUDED_REQUEST_PATHS, endpoint):
        return

    REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()


def request_timing_after_request(scope, status_code, duration):  # noqa: ARG001
    method = scope.get("method", "")
    endpoint = scope.get("path", "")

    if check_if_path_excluded(EXCLUDED_REQUEST_PATHS, endpoint):
        return

    REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


def request_timing_on_error(scope, exc, duration):  # noqa: ARG001
    method = scope.get("method", "")
    endpoint = scope.get("path", "")

    if check_if_path_excluded(EXCLUDED_REQUEST_PATHS, endpoint):
        return

    status_code = getattr(exc, "status_code", 500) or 500

    REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
    REQUEST_ERRORS.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
        error_class=exc.__class__.__name__,
    ).inc()
