from lib.jobs import BaseJob, interval


class RecoverDeadFeedsJob(BaseJob):
    """
    Feed Recovery Job.

    This job is responsible for periodically checking feeds that have been marked as DEAD or FAILING
    to determine if they have become reachable again.

    It runs on a fixed interval of 6 hours

    When a dead feed responds successfully to a lightweight HTTP check, the job automatically
    revives it by resetting its status to ACTIVE, clearing error counters, and allowing it to be
    polled again in the future.
    """

    queue = "maintenance"
    max_attempts = 1
    schedule = interval(hours=6)

    def perform(self) -> None:
        """
        Performs the feed recovery process by checking for dead feeds and attempting to revive them if they are reachable again.
        """

        async def job_coro() -> None:
            try:
                self.logger.info("RecoverDeadFeedsJob: starting dead feeds recovery")

                from bootstrap.database import get_db
                from services.feed_recovery import FeedRecoveryService

                async with get_db() as session:
                    service = FeedRecoveryService(session)
                    await service.run()

                self.logger.info("RecoverDeadFeedsJob: completed dead feeds recovery")
            except Exception as e:
                self.logger.error(f"RecoverDeadFeedsJob: Error occurred while recovering dead feeds - {e}")
                raise e

        self.run_async(job_coro())
