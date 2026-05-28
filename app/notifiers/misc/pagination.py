from lib.notifications import BaseNotification, NotificationMessage
from lib.notifications.transports import SSETransport


class PaginationStreamNotification(BaseNotification):
    """
    Notification for updating pagination components via Server-Sent Events (SSE).

    Transports
    ----------
    This notification is designed to be delivered via Server-Sent Events (SSE) transport,

    Parameters
    ----------
    dom_id: str
        The DOM ID of the pagination component to be updated.

    Example
    -------
    To create a notification for a successful subscription synchronously:

        notification = PaginationStreamNotification(
            dom_id="my-pagination-component"
        )
        await notification.deliver(user) # where `user` is the user object

        notification.deliver_later(user) # where `user` is the user object
    """

    transports = [SSETransport()]

    def __init__(self, *, dom_id: str):
        self.dom_id = dom_id

    def to_notification(self) -> NotificationMessage:
        return NotificationMessage(
            title="Pagination Stream Updated",
            body="The pagination component has been updated.",
            data={"id": self.dom_id, "event": "htmx-pagination:refresh"},
        )

    def serialisable_params(self) -> dict[str, str]:
        return {
            "dom_id": self.dom_id,
        }
