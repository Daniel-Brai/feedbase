from datetime import datetime, timedelta

from lib.jobs import BaseJob, interval
from settings import settings


class SweepArticleJob(BaseJob):
    """
    Article Sweep Job.

    This job is responsible for cleaning up old articles from the database.

    It runs periodically to ensure that the database does not grow indefinitely
    with old articles.

    The retention period is defined by ``settings.APP_ARTICLE_RETENTION_DAYS``. Articles older that is not starred or bookmarked than this period will be deleted.
    """

    queue = "maintenance"
    max_attempts = 1
    schedule = interval(days=settings.APP_ARTICLE_RETENTION_DAYS)

    def perform(self) -> None:
        """
        Perform the article sweep job.
        """

        async def job_coro() -> None:
            try:
                self.logger.info("SweepArticleJob: starting article sweep")

                if settings.APP_ARTICLE_SWEEP_ENABLED is False:
                    self.logger.info("SweepArticleJob: article sweep is disabled, skipping")
                    return

                from bootstrap.database import get_db
                from repositories.article import ArticleRepository

                async with get_db() as db:
                    article_repo = ArticleRepository(db)
                    cutoff_date = datetime.now() - timedelta(days=settings.APP_ARTICLE_RETENTION_DAYS)
                    deleted_count = await article_repo.delete_old_unstarred_unbookmarked_articles(cutoff_date)
                    self.logger.info(f"SweepArticleJob: Deleted {deleted_count} old unstarred/unbookmarked articles.")

            except Exception as e:
                self.logger.error(f"SweepArticleJob: Error occurred during article sweep - {e}")
                raise e

        self.run_async(job_coro())
