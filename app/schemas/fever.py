from typing import Annotated, Literal

from annotated_doc import Doc
from fastapi import Form, Query
from pydantic import BaseModel, computed_field, model_validator

from constants import FEVER_API_VERSION
from models import Article


class FeverForm:
    """
    Represents the form data for the Fever API Request

    Attributes:
        api_key (str): API key for authentication, sent as form data with the key "api_key".
        username (str | None): Username (email) used for Fever login requests.
        password (str | None): Password used for Fever login requests.
    """

    def __init__(
        self,
        *,
        api_key: Annotated[
            str | None,
            Form(),
            Doc(
                """
                The API key for authenticating with the Fever API. This should be sent as form data with the key `api_key`.

                The API key is used to identify and authenticate the user making the request. It should be kept secret and secure, as it grants access to the user's data through the Fever API.
                """
            ),
        ] = None,
        username: Annotated[
            str | None,
            Form(),
            Doc(
                """
                The Fever login username. This is the user's email address.
                """
            ),
        ] = None,
        password: Annotated[
            str | None,
            Form(),
            Doc(
                """
                The Fever login password.
                """
            ),
        ] = None,
    ):
        self.api_key = api_key
        self.username = username
        self.password = password


class FeverQuery(BaseModel):
    """
    Represents the query parameters for the Fever API endpoint.
    """

    api: bool = Query(True, description="No op field to indicate this is an API request for fever")
    feeds: bool = Query(False, description="All subscribed feeds")
    groups: bool = Query(False, description="All feed groups or folders")
    feeds_groups: bool = Query(False, description="Feed-to-group membership mapping")
    items: bool = Query(False, description="A page of items (articles)")
    links: bool = Query(False, description="Recent hot links (Fever extension)")
    unread_item_ids: bool = Query(False, description="Comma-separated unread item IDs")
    saved_item_ids: bool = Query(False, description="Comma-separated saved/starred item IDs")
    action: Literal["login"] | None = Query(None, description="Undocumented Fever action, such as login")

    since_id: int | None = Query(None, description="Items with id greater than since_id (forward paging)")
    max_id: int | None = Query(None, description="Items with id less than max_id (backward paging)")
    with_ids: str | None = Query(None, description="Comma-separated list of specific item IDs to fetch")

    mark: Literal["item", "feed", "group"] | None = Query(None, description="Entity type to mark")
    as_: Literal["read", "unread", "saved", "unsaved"] | None = Query(
        None, alias="as", description="Target state for the mark action"
    )
    id: int | None = Query(None, description="ID of the entity to mark")
    before: int | None = Query(
        None,
        description="Unix timestamp, marks feed or group items older than this as read",
    )

    @model_validator(mode="after")
    def validate_query(self) -> "FeverQuery":
        if self.mark is not None:
            if self.as_ is None:
                raise ValueError("`as` is required when `mark` is present")
            if self.id is None:
                raise ValueError("`id` is required when `mark` is present")

        has_action = any(
            [
                self.api,
                self.feeds,
                self.groups,
                self.feeds_groups,
                self.items,
                self.links,
                self.unread_item_ids,
                self.saved_item_ids,
                self.is_mark_request,
                self.action == "login",
            ]
        )
        if not has_action:
            raise ValueError("At least one Fever API action flag must be present")

        return self

    @computed_field
    @property
    def with_ids_list(self) -> list[int]:
        if not self.with_ids:
            return []
        try:
            return [int(i.strip()) for i in self.with_ids.split(",") if i.strip()]
        except ValueError:
            return []

    @computed_field
    @property
    def is_mark_request(self) -> bool:
        return self.mark is not None


class FeverFeed(BaseModel):
    """
    Schema representing a feed in the Fever API response.

    Attributes:
        id (int): Unique identifier for the feed.
        favicon_id (int): Identifier for the feed's favicon.
        title (str): Title of the feed.
        url (str): URL of the feed.
        site_url (str): URL of the feed's website.
        is_spark (int): Indicates if the feed is a "spark" (Fever extension, always 0 in this implementation).
        last_updated_on_time (int): Unix timestamp of the last update time for the feed.
    """

    id: int
    favicon_id: int
    title: str
    url: str
    site_url: str
    is_spark: int = 0
    last_updated_on_time: int


class FeverGroup(BaseModel):
    """
    Schema representing a feed group (folder) in the Fever API response.

    Attributes:
        id (int): Unique identifier for the group.
        title (str): Title of the group.
    """

    id: int
    title: str


class FeverFeedGroup(BaseModel):
    """
    Schema representing the membership of feeds in groups for the Fever API response.

    Attributes:
        group_id (int): Unique identifier for the group.
        feed_ids (str): Comma-separated string of feed IDs that belong to this group.
    """

    group_id: int
    feed_ids: str


class FeverItem(BaseModel):
    """
    Schema representing an item (article) in the Fever API response.

    Attributes:
        id (int): Unique identifier for the item.
        feed_id (int): Identifier of the feed this item belongs to.
        title (str): Title of the item.
        author (str): Author of the item.
        html (str): HTML content of the item.
        url (str): URL of the item.
        is_saved (int): Indicates if the item is saved/starred (1) or not (0).
        is_read (int): Indicates if the item is read (1) or unread (0).
        created_on_time (int): Unix timestamp of when the item was created.
    """

    id: int
    feed_id: int
    title: str
    author: str
    html: str
    url: str
    is_saved: int
    is_read: int
    created_on_time: int

    @classmethod
    def from_article(cls, article: Article, is_saved: bool, is_read: bool) -> "FeverItem":
        """
        Create a `FeverItem` instance from an Article model instance.
        """

        return FeverItem(
            id=article.id.int,
            feed_id=article.feed_id.int,
            title=article.title or "",
            author=article.author or "",
            html=article.content or article.summary or "",
            url=str(article.url) if article.url else "",
            is_saved=int(is_saved),
            is_read=int(is_read),
            created_on_time=(
                int(article.published_at.timestamp())
                if hasattr(article, "published_at") and article.published_at
                else int(article.created_at.timestamp()) if article.created_at else 0
            ),
        )


class FeverResponseOut(BaseModel):
    """
    Schema representing the overall response structure for the Fever API.

    Fields are only included when the corresponding query flag was present, so we use Optional throughout.

    Attributes:
        api_version (int): The version of the Fever API being used.
        auth (int): Authentication status (1 for authenticated, 0 for not).
        feeds (list[FeverFeed] | None): List of subscribed feeds (if requested).
        feeds_groups (list[FeverFeedGroup] | None): List of feed-to-group memberships (if requested).
        groups (list[FeverGroup] | None): List of feed groups/folders (if requested).
        items (list[FeverItem] | None): List of items/articles (if requested).
        total_items (int | None): Total number of items available (if items were requested).
        unread_item_ids (str | None): Comma-separated string of unread item IDs (if requested).
        saved_item_ids (str | None): Comma-separated string of saved/starred item IDs (if requested).
        last_refreshed_on_time (int | None): Unix timestamp of the last refresh time (if requested).
    """

    model_config = {
        "populate_by_name": True,
    }

    api_version: int = FEVER_API_VERSION
    auth: int

    feeds: list[FeverFeed] = []
    feeds_groups: list[FeverFeedGroup] | None = None
    groups: list[FeverGroup] | None = None
    items: list[FeverItem] | None = None
    total_items: int | None = None
    unread_item_ids: str | None = None
    saved_item_ids: str | None = None
    last_refreshed_on_time: int | None = None
