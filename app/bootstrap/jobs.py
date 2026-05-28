from hooks import job_before_perform, job_on_error, job_on_success
from sqlalchemy import create_engine

from enums import JobBackend
from lib.jobs import CeleryAdapter, DBAdapter
from lib.jobs import configure_jobs as _configure_jobs
from settings import settings


def configure_jobs():
    """
    Configure the job adapter based on the current environment.

    In production, use Celery. In other environments, use the DB adapter for simplicity.

    See :func:`~lib.jobs.configure_jobs` for more details and examples.
    """

    from bootstrap.celery import celery_app

    backend = settings.USE_JOB_BACKEND

    if backend == JobBackend.CELERY:
        adapter = CeleryAdapter(celery_app=celery_app, use_beat=True)
    else:
        adapter = DBAdapter(
            engine=create_engine(str(settings.APP_SQLALCHEMY_DATABASE_SYNC_URI), future=True),
            workers=2,
        )

    return _configure_jobs(
        adapter=adapter,
        modules=[
            "lib.attachments.jobs",
            "lib.auth.jobs",
            "lib.notifications.jobs",
            "jobs.feed",
            "jobs.article",
        ],
        before_perform=[job_before_perform],
        on_success=[job_on_success],
        on_error=[job_on_error],
    )
