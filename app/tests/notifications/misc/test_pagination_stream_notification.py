from unittest.mock import patch

from lib.notifications.transports import SSETransport
from lib.testing import TestNotificationCase, captured_transports
from notifiers import PaginationStreamNotification


class TestPaginationStreamNotification(TestNotificationCase):

    notification_class = PaginationStreamNotification

    async def test_to_notification_returns_expected_message(self):
        notification = self.notification(dom_id="page-list")
        message = notification.to_notification()

        self.assertEqual(message.title, "Pagination Stream Updated")
        self.assertEqual(message.body, "The pagination component has been updated.")
        self.assertEqual(
            message.data,
            {"id": "page-list", "event": "htmx-pagination:refresh"},
        )

    async def test_serialisable_params_contains_dom_id(self):
        notification = self.notification(dom_id="page-list")
        self.assert_params_contain(notification, dom_id="page-list")

    async def test_deliver_uses_sse_transport(self):
        recipient = self.make_recipient()
        notification = self.notification(dom_id="page-list")

        with captured_transports(SSETransport) as delivered:
            await notification.deliver(recipient)

        self.assert_transport_called(delivered, SSETransport)

    async def test_from_params_roundtrip(self):
        notification = self.notification(dom_id="page-list")
        self.assert_roundtrip(notification)

    async def test_deliver_later_dispatches_job(self):
        from lib.notifications.jobs import DeliverNotificationJob

        recipient = self.make_recipient()
        notification = self.notification(dom_id="page-list")

        with patch.object(DeliverNotificationJob, "perform_later") as mock_later:
            notification.deliver_later(recipient)

        mock_later.assert_called_once()
