from typing import Any

from lib.notifications import BaseNotification, NotificationMessage
from lib.notifications.transports import WebPushTransport


class NewArticleNotification(BaseNotification):
    """
    Notification for new articles.

    Transports
    ----------
    This notification is designed to be delivered via Web Push notifications.

    Parameters
    ----------
    no_of_articles: int
        The number of new articles.

    feed_titles: list[str]
        The titles of the feeds that have new articles.

    Example
    -------
    To create a notification for new articles synchronously:

        notification = NewArticleNotification(
            articles_count=5,
            feed_titles=["Hacker News", "TechCrunch"]
        )

        await notification.deliver(user) # where `user` is the user object
        notification.deliver_later(user) # where `user` is the user object
    """

    transports = [
        WebPushTransport(if_=lambda u: u.preferences.get("allow_push_notifications", False)),
    ]

    def __init__(self, *, articles_count: int, feed_titles: list[str]):
        self.articles_count = articles_count
        self.feed_titles = feed_titles

    def to_notification(self) -> NotificationMessage:
        feed_list = ", ".join(self.feed_titles)

        if len(self.feed_titles) > 2:
            preview = ", ".join(self.feed_titles[:2])
            feed_list = f"{preview}, and {len(self.feed_titles) - 2} more"

        article_word = "article" if self.articles_count == 1 else "articles"

        return NotificationMessage(
            title="Fresh reads waiting",
            body=f"{self.articles_count} new {article_word} from {feed_list}. Tap to catch up.",
            vibrate=[200, 100, 200],
        )

    def serialisable_params(self) -> dict[str, Any]:
        return {
            "articles_count": self.articles_count,
            "feed_titles": self.feed_titles,
        }
