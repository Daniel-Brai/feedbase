from lib.monitoring.prometheus import counter, gauge, histogram

JOBS_PROCESSED = counter(
    "jobs_processed_total",
    "Total number of jobs processed",
    ["name", "status"],
)

JOBS_DURATION = histogram(
    "jobs_duration_seconds",
    "Time spent processing jobs in seconds",
    ["name", "status"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
)

REQUEST_ERRORS = counter(
    "request_errors_total",
    "Total number of request errors by endpoint and error type",
    labels=["method", "endpoint", "status_code", "error_class"],
)


REQUESTS_IN_PROGRESS = gauge(
    "requests_in_progress",
    "Number of requests currently being processed",
    labels=["method", "endpoint"],
)

TEMPLATE_RENDER_DURATION = histogram(
    "template_render_seconds",
    "Time spent rendering templates",
    labels=["name"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
)
