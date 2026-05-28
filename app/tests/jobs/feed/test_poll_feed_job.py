from unittest.mock import AsyncMock

import pytest

from jobs.feed import PollFeedJob
from lib.testing import TestJobCase


class TestPollFeedJob(TestJobCase):

    job_class = PollFeedJob

    async def test_delegates_to_feed_poller_service(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.feed_poller.FeedPollerService"
        ) as MockPoller:
            MockGetDb.return_value = self.db
            MockPoller.return_value.run = AsyncMock()

            self.make_job().perform()

        MockGetDb.assert_called_once()
        MockPoller.return_value.run.assert_awaited_once()

    async def test_raises_when_get_db_fails(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.feed_poller.FeedPollerService"
        ) as MockPoller:
            MockGetDb.side_effect = Exception("DB unavailable")
            MockPoller.return_value.run = AsyncMock()

            with pytest.raises(Exception, match="DB unavailable"):
                self.make_job().perform()

        MockGetDb.assert_called_once()
        MockPoller.return_value.run.assert_not_awaited()

    async def test_raises_on_service_error(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.feed_poller.FeedPollerService"
        ) as MockPoller:
            MockGetDb.return_value = self.db
            MockPoller.return_value.run = AsyncMock(side_effect=Exception("Poller exploded"))

            with pytest.raises(Exception, match="Poller exploded"):
                self.make_job().perform()

        MockGetDb.assert_called_once()
        MockPoller.return_value.run.assert_awaited_once()
