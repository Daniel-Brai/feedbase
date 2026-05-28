from unittest.mock import AsyncMock

import pytest

from jobs.feed import RecoverDeadFeedsJob
from lib.testing import TestJobCase


class TestRecoverDeadFeedsJob(TestJobCase):

    job_class = RecoverDeadFeedsJob

    async def test_delegates_to_feed_recovery_service(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.feed_recovery.FeedRecoveryService"
        ) as MockService:
            MockGetDb.return_value = self.db
            MockService.return_value.run = AsyncMock()

            self.make_job().perform()

        MockGetDb.assert_called_once()
        MockService.return_value.run.assert_awaited_once()

    async def test_raises_when_get_db_fails(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.feed_recovery.FeedRecoveryService"
        ) as MockService:
            MockGetDb.side_effect = Exception("DB unavailable")
            MockService.return_value.run = AsyncMock()

            with pytest.raises(Exception, match="DB unavailable"):
                self.make_job().perform()

        MockGetDb.assert_called_once()
        MockService.return_value.run.assert_not_awaited()

    async def test_raises_on_service_error(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.feed_recovery.FeedRecoveryService"
        ) as MockService:
            MockGetDb.return_value = self.db
            MockService.return_value.run = AsyncMock(side_effect=Exception("Recovery failed"))

            with pytest.raises(Exception, match="Recovery failed"):
                self.make_job().perform()

        MockGetDb.assert_called_once()
        MockService.return_value.run.assert_awaited_once()
