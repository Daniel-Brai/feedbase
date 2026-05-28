import xml.etree.ElementTree as ET

import pytest

from constants import OPML_DOCS_SCHEMA_URL
from lib.ext.fastapi import ServiceError
from lib.testing.services import TestServiceIntegrationCase
from services.opml_exporter import OPMLExporterService
from tests.conftest import TestAsyncDBEngine, TestAsyncDBSession
from tests.factories import FeedFactory, FeedSubscriptionFactory, FolderFactory, UserFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestOPMLExporterService(TestServiceIntegrationCase):

    service_class = OPMLExporterService
    db_engine = TestAsyncDBEngine
    db_session_factory = TestAsyncDBSession

    async def test_run_exports_user_subscriptions_with_folders(self) -> None:
        user = await UserFactory.create(
            name="Jane Subscriber",
            email="jane@example.org",
        )

        root_feed = await FeedFactory.create(
            url="https://example.org/root.xml",
            title="Root Feed",
            site_url="https://example.org",
            description="Root feed description.",
        )
        news_folder = await FolderFactory.create(user=user, name="News")
        tech_folder = await FolderFactory.create(user=user, name="Tech")
        news_feed = await FeedFactory.create(
            url="https://example.org/news.xml",
            title="News Feed",
            site_url="https://news.example.org",
            description=None,
        )
        custom_feed = await FeedFactory.create(
            url="https://example.org/custom.xml",
            title="Custom Feed Title",
            site_url=None,
            description="Custom feed description.",
        )
        tech_feed = await FeedFactory.create(
            url="https://example.org/tech.xml",
            title="Tech Feed Title",
            site_url=None,
            description="Tech feed description.",
        )

        await FeedSubscriptionFactory.create(user=user, feed=root_feed)
        await FeedSubscriptionFactory.create(user=user, feed=news_feed, folder=news_folder)
        await FeedSubscriptionFactory.create(
            user=user,
            feed=custom_feed,
            folder=news_folder,
            title="My custom subscription",
        )
        await FeedSubscriptionFactory.create(user=user, feed=tech_feed, folder=tech_folder)

        opml_xml = await self.service.run(user.id)
        root = ET.fromstring(opml_xml)

        assert root.tag == "opml"
        assert root.attrib.get("version") == "2.0"

        head = root.find("head")
        assert head is not None

        title_el = head.find("title")
        assert title_el is not None
        assert "Jane Subscriber" in (title_el.text or "")

        owner_email_el = head.find("ownerEmail")
        assert owner_email_el is not None
        assert owner_email_el.text == "jane@example.org"

        docs_el = head.find("docs")
        assert docs_el is not None
        assert docs_el.text == OPML_DOCS_SCHEMA_URL

        date_created_el = head.find("dateCreated")
        assert date_created_el is not None
        assert date_created_el.text is not None

        date_modified_el = head.find("dateModified")
        assert date_modified_el is not None
        assert date_modified_el.text is not None

        body = root.find("body")
        assert body is not None

        outlines = list(body.findall("outline"))
        assert len(outlines) == 3

        root_outlines = [o for o in outlines if o.attrib.get("xmlUrl") == root_feed.url]
        assert len(root_outlines) == 1

        root_outline = root_outlines[0]
        assert root_outline.attrib["text"] == "Root Feed"
        assert root_outline.attrib["title"] == "Root Feed"
        assert root_outline.attrib["htmlUrl"] == "https://example.org"
        assert root_outline.attrib["description"] == "Root feed description."
        assert "created" in root_outline.attrib

        folder_outlines = [o for o in outlines if o.attrib.get("text") in {"News", "Tech"}]
        assert len(folder_outlines) == 2

        news_outline = next(o for o in folder_outlines if o.attrib["text"] == "News")
        news_children = list(news_outline.findall("outline"))
        assert {child.attrib["xmlUrl"] for child in news_children} == {
            news_feed.url,
            custom_feed.url,
        }
        assert any(child.attrib["text"] == "News Feed" for child in news_children)
        assert any(child.attrib["text"] == "My custom subscription" for child in news_children)

        tech_outline = next(o for o in folder_outlines if o.attrib["text"] == "Tech")
        tech_children = list(tech_outline.findall("outline"))
        assert len(tech_children) == 1
        assert tech_children[0].attrib["xmlUrl"] == tech_feed.url
        assert tech_children[0].attrib["text"] == "Tech Feed Title"
        assert tech_children[0].attrib["description"] == "Tech feed description."
        assert "htmlUrl" not in tech_children[0].attrib
        assert "created" in tech_children[0].attrib

    async def test_run_exports_subscription_without_title_uses_url(self) -> None:
        user = await UserFactory.create(name="Url User", email="url@example.org")
        no_title_feed = await FeedFactory.create(
            url="https://example.org/no-title.xml",
            title=None,
            site_url=None,
            description=None,
        )

        await FeedSubscriptionFactory.create(user=user, feed=no_title_feed)

        opml_xml = await self.service.run(user.id)
        root = ET.fromstring(opml_xml)
        body = root.find("body")
        assert body is not None

        outlines = list(body.findall("outline"))
        assert len(outlines) == 1
        no_title_outline = outlines[0]
        assert no_title_outline.attrib["xmlUrl"] == no_title_feed.url
        assert no_title_outline.attrib["text"] == no_title_feed.url
        assert "title" not in no_title_outline.attrib
        assert "description" not in no_title_outline.attrib
        assert "htmlUrl" not in no_title_outline.attrib

    async def test_run_truncates_description_to_500_characters(self) -> None:
        user = await UserFactory.create(name="Truncate User", email="truncate@example.org")
        long_description = "a" * 600
        long_feed = await FeedFactory.create(
            url="https://example.org/long-description.xml",
            title="Long Feed",
            site_url="https://example.org/long",
            description=long_description,
        )

        await FeedSubscriptionFactory.create(user=user, feed=long_feed)

        opml_xml = await self.service.run(user.id)
        root = ET.fromstring(opml_xml)
        body = root.find("body")
        assert body is not None

        long_outline = next(o for o in body.findall("outline") if o.attrib["xmlUrl"] == long_feed.url)
        assert len(long_outline.attrib["description"]) == 500
        assert long_outline.attrib["description"] == long_description[:500]

    async def test_run_raises_service_error_for_user_with_no_subscriptions(
        self,
    ) -> None:
        user = await UserFactory.create(name="Empty User", email="empty@example.org")

        with pytest.raises(ServiceError) as exc_info:
            await self.service.run(user.id)

        assert exc_info.value.status_code == 404
        assert "No subscriptions found for user" in str(exc_info.value)

    async def test_run_raises_service_error_for_missing_user(self) -> None:
        with pytest.raises(ServiceError) as exc_info:
            await self.service.run(-1)

        assert "User not found" in str(exc_info.value)
