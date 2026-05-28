import time

from constants import JOBS_DURATION, JOBS_PROCESSED


def job_before_perform(job):
    job._metrics_started_at = time.perf_counter()


def job_on_success(job):
    duration = time.perf_counter() - getattr(job, "_metrics_started_at", time.perf_counter())
    JOBS_DURATION.labels(name=job.__class__.__name__, status="success").observe(duration)
    JOBS_PROCESSED.labels(name=job.__class__.__name__, status="success").inc()


def job_on_error(job, exc):  # noqa: ARG001
    duration = time.perf_counter() - getattr(job, "_metrics_started_at", time.perf_counter())
    JOBS_DURATION.labels(name=job.__class__.__name__, status="error").observe(duration)
    JOBS_PROCESSED.labels(name=job.__class__.__name__, status="error").inc()
