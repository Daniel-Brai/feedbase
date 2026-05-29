from datetime import timedelta
from unittest.mock import MagicMock, patch

from lib.notifications.transports import WebPushTransport
from lib.testing import TestNotificationCase, captured_transports
from notifiers import NewArticleNotification


class TestNewArticleNotification(TestNotificationCase):

    notification_class = NewArticleNotification

    async def test_title_is_always_fresh_reads_waiting(self):
        notification = self.notification(articles_count=3, feed_titles=["HN"])
        msg = notification.to_notification()
        self.assertEqual(msg.title, "Fresh reads waiting")

    async def test_body_uses_singular_article_for_one(self):
        notification = self.notification(articles_count=1, feed_titles=["HN"])
        msg = notification.to_notification()
        self.assertIn("1 new article", msg.body)
        self.assertNotIn("articles", msg.body)

    async def test_body_uses_plural_articles_for_many(self):
        notification = self.notification(articles_count=5, feed_titles=["HN"])
        msg = notification.to_notification()
        self.assertIn("5 new articles", msg.body)

    async def test_body_shows_single_feed_title(self):
        notification = self.notification(articles_count=2, feed_titles=["Hacker News"])
        msg = notification.to_notification()
        self.assertIn("Hacker News", msg.body)

    async def test_body_shows_two_feed_titles_without_truncation(self):
        notification = self.notification(
            articles_count=3,
            feed_titles=["Hacker News", "TechCrunch"],
        )
        msg = notification.to_notification()
        self.assertIn("Hacker News", msg.body)
        self.assertIn("TechCrunch", msg.body)
        self.assertNotIn("more", msg.body)

    async def test_body_truncates_more_than_two_feeds(self):
        notification = self.notification(
            articles_count=10,
            feed_titles=["HN", "TC", "Ars Technica", "The Verge"],
        )
        msg = notification.to_notification()
        self.assertIn("HN", msg.body)
        self.assertIn("TC", msg.body)
        self.assertIn("2 more", msg.body)
        self.assertNotIn("Ars Technica", msg.body)
        self.assertNotIn("The Verge", msg.body)

    async def test_body_truncates_exactly_three_feeds(self):
        notification = self.notification(
            articles_count=3,
            feed_titles=["A", "B", "C"],
        )
        msg = notification.to_notification()
        self.assertIn("1 more", msg.body)

    async def test_serialisable_params_contains_articles_count(self):
        notification = self.notification(articles_count=7, feed_titles=["HN"])
        self.assert_params_contain(notification, articles_count=7)

    async def test_serialisable_params_contains_feed_titles(self):
        titles = ["HN", "TC"]
        notification = self.notification(articles_count=2, feed_titles=titles)
        self.assert_params_contain(notification, feed_titles=titles)

    async def test_from_params_roundtrip(self):
        notification = self.notification(
            articles_count=4,
            feed_titles=["HN", "TC", "Ars"],
        )
        self.assert_roundtrip(notification)

    async def test_deliver_calls_web_push_when_guard_passes(self):
        recipient = self.make_recipient(preferences={"allow_push_notifications": True})
        notification = self.notification(articles_count=3, feed_titles=["HN"])

        with captured_transports(WebPushTransport) as delivered:
            await notification.deliver(recipient)

        self.assert_transport_called(delivered, WebPushTransport)

    async def test_deliver_skips_web_push_when_guard_fails(self):
        recipient = self.make_recipient(preferences={"allow_push_notifications": False})
        notification = self.notification(articles_count=3, feed_titles=["HN"])

        with captured_transports(WebPushTransport) as delivered:
            await notification.deliver(recipient)

        self.assert_transport_not_called(delivered, WebPushTransport)

    async def test_deliver_skips_web_push_when_preference_absent(self):
        recipient = self.make_recipient(preferences={})
        notification = self.notification(articles_count=1, feed_titles=["HN"])

        with captured_transports(WebPushTransport) as delivered:
            await notification.deliver(recipient)

        self.assert_transport_not_called(delivered, WebPushTransport)

    async def test_deliver_to_multiple_recipients(self):
        recipients = [self.make_recipient(id=i, preferences={"allow_push_notifications": True}) for i in range(3)]
        notification = self.notification(articles_count=5, feed_titles=["HN"])

        with captured_transports(WebPushTransport) as delivered:
            await notification.deliver(recipients)

        self.assert_transport_called(delivered, WebPushTransport, count=3)

    async def test_message_passed_to_transport_has_correct_title(self):
        recipient = self.make_recipient(preferences={"allow_push_notifications": True})
        notification = self.notification(articles_count=2, feed_titles=["HN"])

        with captured_transports(WebPushTransport) as delivered:
            await notification.deliver(recipient)

        self.assert_message_title(delivered, "Fresh reads waiting")

    async def test_deliver_later_dispatches_job(self):
        from lib.notifications.jobs import DeliverNotificationJob

        recipient = self.make_recipient()
        notification = self.notification(articles_count=3, feed_titles=["HN"])

        with patch.object(DeliverNotificationJob, "perform_later") as mock_later:
            notification.deliver_later(recipient)

        mock_later.assert_called_once()

    async def test_deliver_later_includes_correct_notification_class_path(self):
        from lib.notifications.jobs import DeliverNotificationJob

        recipient = self.make_recipient()
        notification = self.notification(articles_count=3, feed_titles=["HN"])

        with patch.object(DeliverNotificationJob, "perform_later") as mock_later:
            notification.deliver_later(recipient)

        kwargs = mock_later.call_args.kwargs
        self.assertIn("NewArticleNotification", kwargs["notification_class"])

    async def test_deliver_later_includes_serialised_params(self):
        from lib.notifications.jobs import DeliverNotificationJob

        recipient = self.make_recipient()
        notification = self.notification(articles_count=5, feed_titles=["HN", "TC"])

        with patch.object(DeliverNotificationJob, "perform_later") as mock_later:
            notification.deliver_later(recipient)

        kwargs = mock_later.call_args.kwargs
        self.assertEqual(kwargs["params"]["articles_count"], 5)
        self.assertEqual(kwargs["params"]["feed_titles"], ["HN", "TC"])

    async def test_deliver_later_handles_multiple_recipients(self):
        from lib.notifications.jobs import DeliverNotificationJob

        recipients = [
            self.make_recipient(id=1),
            self.make_recipient(id=2),
        ]
        notification = self.notification(articles_count=3, feed_titles=["HN"])

        with patch.object(DeliverNotificationJob, "perform_later") as mock_later:
            notification.deliver_later(recipients)

        self.assertEqual(mock_later.call_count, 2)

    async def test_set_proxies_timing_options_to_deliver_later(self):
        from lib.notifications.jobs import DeliverNotificationJob

        recipient = self.make_recipient()
        notification = self.notification(articles_count=3, feed_titles=["HN"])
        proxy = MagicMock()

        with patch.object(DeliverNotificationJob, "set", return_value=proxy) as mock_set:
            notification.set(wait=timedelta(minutes=20)).deliver_later(recipient)

        mock_set.assert_called_once_with(wait=timedelta(minutes=20), wait_until=None)
        proxy.perform_later.assert_called_once()
