import xml.etree.ElementTree as ET
from uuid import UUID

from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from jobs import FetchFeedJob
from lib.ext.fastapi import Service, ServiceError
from repositories import FeedRepository, FeedSubscriptionRepository, FolderRepository
from schemas import OPMLImportResultOut


class OPMLImporterService(Service):
    """
    Service for importing subscriptions from an OPML file
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.feed_repo = FeedRepository(db)
        self.feed_subscription_repo = FeedSubscriptionRepository(db)
        self.folder_repo = FolderRepository(db)

    async def run(self, user_id: int, opml_content: bytes) -> OPMLImportResultOut:
        """
        Parse OPML content, create folders, and subscribe the user to all feeds.

        Args:
            user_id (int): ID of the user importing subscriptions.
            opml_content (bytes): Raw bytes of the uploaded OPML file.

        Returns:
            OPMLImportResultOut: Result with counts of added, skipped, failed feeds,folders created, and any error messages.
        """

        try:
            root = ET.fromstring(opml_content)
        except ET.ParseError as e:
            result = OPMLImportResultOut(added=0, skipped=0, failed=0, folders_created=0)
            result.errors = [f"Invalid OPML file: {e}"]
            return result

        version = root.get("version", "1.0")
        if version not in ("1.0", "1.1", "2.0"):
            self.logger.warning("Unknown OPML version %r — attempting parse anyway", version)

        body = root.find("body")
        if body is None:
            result = OPMLImportResultOut(added=0, skipped=0, failed=0, folders_created=0)
            result.errors = ["OPML file has no <body> element"]
            return result

        result = OPMLImportResultOut(added=0, skipped=0, failed=0, folders_created=0)

        try:
            async with self.transaction():
                await self._walk_outlines(body, user_id, result, None)

            if result.errors and result.added == 0 and result.skipped == 0 and result.failed == 0:
                raise ServiceError(
                    "Failed to import OPML file " + "; ".join(result.errors),
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            return result
        except Exception as e:
            self.logger.error(f"OPML import transaction failed: {str(e)}", exc_info=e)
            raise ServiceError("Failed to import OPML file. Please try again later.") from e

    async def _walk_outlines(
        self,
        parent_el: ET.Element,
        user_id: int,
        result: OPMLImportResultOut,
        folder_id: UUID | None,
    ) -> None:
        for outline in parent_el.findall("outline"):
            outline_type = (outline.get("type") or "").lower()
            text = outline.get("text", "").strip()
            xml_url = outline.get("xmlUrl", "").strip()

            is_feed = outline_type in ("rss", "atom", "feed", "pie") or bool(xml_url)

            if is_feed and xml_url:
                await self._import_feed(
                    url=xml_url,
                    text=text,
                    user_id=user_id,
                    result=result,
                    folder_id=folder_id,
                    outline=outline,
                )
            elif outline.find("outline") is not None:
                folder = await self._get_or_create_folder(
                    name=text or "Imported folder",
                    user_id=user_id,
                    result=result,
                    parent_id=folder_id,
                )

                await self._walk_outlines(
                    parent_el=outline,
                    user_id=user_id,
                    result=result,
                    folder_id=folder.id,
                )
            else:
                self.logger.debug(f"Skipping non-feed outline: text={text!r} type={outline_type!r}")

    async def _import_feed(
        self,
        url: str,
        text: str,
        user_id: int,
        result: OPMLImportResultOut,
        folder_id: UUID | None,
        outline: ET.Element,
    ) -> None:
        try:
            feed = await self.feed_repo.get_by(url=url)
            if not feed:
                feed_title = outline.get("title") or text or url
                html_url = outline.get("htmlUrl")
                feed = await self.feed_repo.create(
                    {
                        "url": url,
                        "site_url": html_url,
                        "title": feed_title,
                    }
                )
                FetchFeedJob.perform_later(feed_id=feed.id, user_id=user_id).with_session(self.db)

            existing_sub = await self.feed_subscription_repo.get_by(user_id=user_id, feed_id=feed.id)
            if existing_sub:
                result.skipped += 1
                return

            custom_title = text if text and text != feed.title else None
            await self.feed_subscription_repo.create(
                {
                    "user_id": user_id,
                    "feed_id": feed.id,
                    "folder_id": folder_id,
                    "title": custom_title,
                }
            )
            result.added += 1
        except Exception as e:
            self.logger.error(f"Failed to import feed {url}: {str(e)}", exc_info=e)
            result.failed += 1
            result.errors.append(f"{url}: {str(e)}")

    async def _get_or_create_folder(
        self,
        name: str,
        user_id: int,
        result: OPMLImportResultOut,
        parent_id: UUID | None = None,
    ):
        folder = await self.folder_repo.get_by(user_id=user_id, name=name, parent_id=parent_id)
        if folder:
            return folder

        folder = await self.folder_repo.create(
            {
                "user_id": user_id,
                "name": name,
                "parent_id": parent_id,
            }
        )
        result.folders_created += 1
        return folder
