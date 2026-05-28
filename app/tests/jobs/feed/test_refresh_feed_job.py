from unittest.mock import AsyncMock

import pytest

from jobs.feed import RefreshFeedJob
from lib.testing import TestJobCase


class TestRefreshFeedJob(TestJobCase):

    job_class = RefreshFeedJob

    async def test_delegates_to_feed_poller_service_and_sends_notifications(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "repositories.user.UserRepository"
        ) as MockUserRepo, self.patch("services.feed_poller.FeedPollerService") as MockPoller, self.patch(
            "jobs.feed.refresh.PaginationStreamNotification"
        ) as MockNotification:
            MockGetDb.return_value = self.db
            MockUserRepo.return_value.get = AsyncMock(return_value={"id": 123})
            MockPoller.return_value.run = AsyncMock()
            MockNotification.return_value.deliver = AsyncMock()

            self.make_job().perform(user_id=123)

        MockGetDb.assert_called_once()
        MockPoller.return_value.run.assert_awaited_once()
        MockUserRepo.return_value.get.assert_awaited_once_with(123)
        self.assertEqual(MockNotification.call_count, 2)

        MockNotification.assert_any_call(dom_id="subscriptions")
        MockNotification.assert_any_call(dom_id="articles")
        self.assertEqual(MockNotification.return_value.deliver.call_count, 2)

    async def test_raises_on_service_error(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "repositories.user.UserRepository"
        ) as MockUserRepo, self.patch("services.feed_poller.FeedPollerService") as MockPoller, self.patch(
            "jobs.feed.refresh.PaginationStreamNotification"
        ) as MockNotification:
            MockGetDb.return_value = self.db
            MockUserRepo.return_value.get = AsyncMock(return_value={"id": 123})
            MockPoller.return_value.run = AsyncMock(side_effect=Exception("Refresh failed"))
            MockNotification.return_value.deliver = AsyncMock()

            with pytest.raises(Exception, match="Refresh failed"):
                self.make_job().perform(user_id=123)

        MockGetDb.assert_called_once()
        MockPoller.return_value.run.assert_awaited_once()

    async def test_does_not_send_notifications_when_user_missing(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "repositories.user.UserRepository"
        ) as MockUserRepo, self.patch("services.feed_poller.FeedPollerService") as MockPoller, self.patch(
            "jobs.feed.refresh.PaginationStreamNotification"
        ) as MockNotification:
            MockGetDb.return_value = self.db
            MockUserRepo.return_value.get = AsyncMock(return_value=None)
            MockPoller.return_value.run = AsyncMock()
            MockNotification.return_value.deliver = AsyncMock()

            self.make_job().perform(user_id=123)

        MockGetDb.assert_called_once()
        MockPoller.return_value.run.assert_awaited_once()

        self.assertEqual(MockNotification.call_count, 0)
        self.assertEqual(MockNotification.return_value.deliver.call_count, 0)
