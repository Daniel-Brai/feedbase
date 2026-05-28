from lib.workers import create_celery_app
from settings import settings

celery_app = create_celery_app(
    broker_url=str(settings.CELERY_BROKER_DSN),
    result_backend=str(settings.CELERY_BROKER_DSN),
    results_expires=5 * 60,  # 5 minutes
)
