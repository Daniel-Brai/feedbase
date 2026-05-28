import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import format_datetime
from xml.dom import minidom

from fastapi import status
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from constants import OPML_DOCS_SCHEMA_URL
from lib.ext.fastapi import IORunnableService, ServiceError
from models import FeedSubscription, User
from repositories import FeedSubscriptionRepository, UserRepository


class OPMLExporterService(IORunnableService):
    """
    Service for exporting user subscriptions in OPML format.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.feed_subscription_repo = FeedSubscriptionRepository(db)
        self.user_repo = UserRepository(db)

    async def run(self, user_id: int) -> str:
        """
        Export the user's subscriptions in OPML format.

        Args:
            user_id (int): The ID of the user whose subscriptions are to be exported.

        Returns:
            str: The OPML XML string representing the user's subscriptions or empty string
        """

        user = await self.user_repo.get(user_id)
        if not user:
            raise ServiceError("User not found")

        return await self._build_opml_feed(user)

    def _rfc822(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        return format_datetime(dt, usegmt=True)

    def _sub(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        el = ET.SubElement(parent, tag)
        el.text = text
        return el

    async def _build_opml_feed(self, user: User) -> str:
        try:
            user_subscriptions = (
                await self.feed_subscription_repo.query()
                .where(col(FeedSubscription.user_id) == user.id)
                .selectinload(FeedSubscription.folder)
                .selectinload(FeedSubscription.feed)
                .all()
            )

            if not user_subscriptions:
                raise ServiceError(
                    "No subscriptions found for user",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            now = datetime.now(UTC)

            root = ET.Element("opml", version="2.0")
            head = ET.SubElement(root, "head")

            title = f"{user.get_display_name()}'s Feedbase subscriptions"
            self._sub(head, "title", title)
            self._sub(head, "dateCreated", self._rfc822(now))
            self._sub(head, "dateModified", self._rfc822(now))
            self._sub(head, "ownerName", user.get_display_name())
            self._sub(head, "ownerEmail", user.email)
            self._sub(head, "docs", OPML_DOCS_SCHEMA_URL)

            body = ET.SubElement(root, "body")

            folders: dict[str | None, list] = {}
            for sub in user_subscriptions:
                folder_name = sub.folder.name if sub.folder else None
                folders.setdefault(folder_name, []).append(sub)

            for sub in folders.pop(None, []):
                self._feed_outline(body, sub)

            for folder_name, subs in folders.items():
                if folder_name:
                    container = ET.SubElement(body, "outline", text=folder_name)
                else:
                    container = body

                for sub in subs:
                    self._feed_outline(container, sub)

            rough = ET.tostring(root, encoding="unicode", xml_declaration=False)
            dom = minidom.parseString(rough)
            pretty = dom.toprettyxml(indent="  ", encoding=None)
            lines = pretty.split("\n")
            if lines[0].startswith("<?xml"):
                lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'

            return "\n".join(lines)
        except ServiceError:
            self.logger.error(
                "Service error while building OPML feed for user %d",
                user.id,
                exc_info=True,
            )
            raise

        except Exception as e:
            self.logger.error("Failed to build OPML feed", error=str(e), exc_info=e)
            raise ServiceError("Failed to build OPML feed") from e

    def _feed_outline(self, parent: ET.Element, sub: FeedSubscription) -> ET.Element:
        feed = sub.feed
        attrs = {
            "type": "rss",
            "text": sub.title or feed.title or feed.url,
            "xmlUrl": feed.url,
        }

        if feed.title:
            attrs["title"] = feed.title

        if feed.site_url:
            attrs["htmlUrl"] = feed.site_url

        if feed.description:
            attrs["description"] = feed.description[:500]

        if sub.created_at:
            attrs["created"] = self._rfc822(sub.created_at)

        return ET.SubElement(parent, "outline", attrib=attrs)
