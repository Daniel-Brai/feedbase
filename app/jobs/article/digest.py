from lib.jobs import BaseJob, interval


class SendArticleDigestJob(BaseJob):
    """
    Article Digest Job.

    This job is responsible for generating digests of articles based on user's preferences.

    It runs periodically (e.g., daily) to compile a list of relevant articles for each user and sends out email notifications with the digest. The digest may include articles from
    """

    queue = "mailer"
    max_attempts = 3
    schedule = interval(hours=1)

    def perform(self) -> None:
        """
        Perform the sending of article digests to users.
        """

        async def job_coro() -> None:
            from bootstrap.database import get_db
            from services.article_digestor import ArticleDigestService

            async with get_db() as session:
                service = ArticleDigestService(session)
                await service.run()

        self.run_async(job_coro())
