from datetime import UTC, datetime
from uuid import UUID

from fastapi import Response
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from constants import FEVER_ITEMS_PAGE_SIZE
from helpers import generate_fever_key
from lib.auth.config import get_hasher
from lib.ext.fastapi import Service
from models import Article, ArticleStatus, Feed, FeedSubscription, User
from repositories import (
    ArticleRepository,
    ArticleStatusRepository,
    FeedRepository,
    FeedSubscriptionRepository,
    FolderRepository,
    UserRepository,
)
from schemas import FeverFeed, FeverFeedGroup, FeverForm, FeverGroup, FeverItem, FeverQuery, FeverResponseOut


class FeverService(Service):
    """
    Service for managing Fever API operations
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)

        self.feed_repo = FeedRepository(db)
        self.feed_subscription_repo = FeedSubscriptionRepository(db)
        self.article_repo = ArticleRepository(db)
        self.article_status_repo = ArticleStatusRepository(db)
        self.folder_repo = FolderRepository(db)
        self.user_repo = UserRepository(db)

    async def handle_request(
        self,
        q: FeverQuery | None,
        f: FeverForm,
    ) -> FeverResponseOut:
        """
        Handle a Fever API request based on the provided query parameters and form data

        Args:
            q (FeverQuery | None): The parsed query parameters from the Fever request or None if validation failed.
            f (FeverForm): The parsed form data from the Fever request.

        Returns:
            FeverResponseOut: The response to be returned to the client based on the Fever API specifications
        """

        if q and q.action == "login":
            return await self._handle_login(q, f)

        api_key = f.api_key

        if not api_key:
            return FeverResponseOut(auth=0)

        user = await self._authenticate(api_key)

        if user is None:
            return FeverResponseOut(auth=0)

        response = FeverResponseOut(auth=1)

        if q is None:
            self.logger.warning("Invalid Fever query parameters", api_key=api_key)
            return response

        try:
            last_refresh = await self.feed_repo.get_fever_last_refresh(user.id)
            if last_refresh is not None:
                response.last_refreshed_on_time = last_refresh
        except Exception as exc:
            self.logger.error(
                "Failed to load fever last refresh",
                user_id=user.id,
                error=str(exc),
                exc_info=exc,
            )

        if q.is_mark_request:
            try:
                await self._handle_mark(q, user)
            except Exception as exc:
                self.logger.error(
                    "Failed to process fever mark request",
                    user_id=user.id,
                    mark=q.mark,
                    as_=q.as_,
                    id=q.id,
                    error=str(exc),
                    exc_info=exc,
                )
            return response

        if q.feeds or q.feeds_groups or q.groups:
            try:
                all_feeds = await self.feed_subscription_repo.get_user_feeds(user.id)

                if q.feeds:
                    response.feeds = [
                        FeverFeed(
                            id=feed.id.int,
                            favicon_id=feed.id.int,
                            title=feed.title or "",
                            url=feed.url,
                            site_url=feed.site_url or feed.url,
                            is_spark=int(feed.is_spark),
                            last_updated_on_time=(int(feed.updated_at.timestamp()) if feed.updated_at else 0),
                        )
                        for feed in all_feeds
                    ]

                mapping = await self.feed_subscription_repo.get_fever_user_feed_groups(user.id)
                if q.feeds_groups or q.groups:
                    response.feeds_groups = [
                        FeverFeedGroup(
                            group_id=gid,
                            feed_ids=",".join(str(fid) for fid in fids),
                        )
                        for gid, fids in mapping.items()
                    ]
            except Exception as exc:
                self.logger.error(
                    "Failed to load fever feed data",
                    user_id=user.id,
                    error=str(exc),
                    exc_info=exc,
                )

        if q.groups:
            try:
                folders = await self.folder_repo.get_user_folders(user.id)

                response.groups = [FeverGroup(id=0, title="Uncategorised")] + [
                    FeverGroup(id=f.id.int, title=f.name) for f in folders
                ]
            except Exception as exc:
                self.logger.error(
                    "Failed to load fever groups",
                    user_id=user.id,
                    error=str(exc),
                    exc_info=exc,
                )

        if q.items:
            try:
                articles = await self.article_repo.get_fever_articles(
                    user_id=user.id,
                    limit=FEVER_ITEMS_PAGE_SIZE,
                    with_ids_list=q.with_ids_list if q.with_ids else None,
                    since_id=q.since_id,
                    max_id=q.max_id,
                )

                article_ids = [a.id for a in articles]
                statuses = (
                    await self.article_status_repo.query()
                    .where(
                        col(ArticleStatus.article_id).in_(article_ids),
                        col(ArticleStatus.user_id) == user.id,
                    )
                    .all()
                    if article_ids
                    else []
                )

                status_map = {st.article_id: st for st in statuses}

                items = []
                for a in articles:
                    st = status_map.get(a.id)
                    is_read = st.is_read if st else False
                    is_saved = st.is_starred if st else False
                    items.append(FeverItem.from_article(a, is_saved, is_read))

                response.items = items
                response.total_items = len(articles)
            except Exception as exc:
                self.logger.error(
                    "Failed to load fever items",
                    user_id=user.id,
                    error=str(exc),
                    exc_info=exc,
                )
                response.items = []
                response.total_items = 0

        if q.unread_item_ids:
            try:
                unread_ids = await self.article_repo.get_unread_article_ids(user.id)
                response.unread_item_ids = ",".join(str(uid.int) for uid in unread_ids)
            except Exception as exc:
                self.logger.error(
                    "Failed to load fever unread item ids",
                    user_id=user.id,
                    error=str(exc),
                    exc_info=exc,
                )

        if q.saved_item_ids:
            try:
                saved_ids = await self.article_repo.get_saved_article_ids(user.id)
                response.saved_item_ids = ",".join(str(uid.int) for uid in saved_ids)
            except Exception as exc:
                self.logger.error(
                    "Failed to load fever saved item ids",
                    user_id=user.id,
                    error=str(exc),
                    exc_info=exc,
                )

        return response

    async def post_process_response(
        self,
        q: FeverQuery | None,
        f: FeverForm,
        result: FeverResponseOut,
        response: Response,
    ) -> Response:
        """
        Perform any necessary post-processing on the response before it is returned to the client.
        """

        if q and q.action == "login" and f.username is not None and result.auth == 1:
            user = await self.user_repo.get_by(email=f.username)
            if user and user.fever_key:
                response.set_cookie("fever_auth", user.fever_key)

        return response

    async def _authenticate(self, api_key: str) -> User | None:
        """
        Authenticate the user based on the provided Fever API key. Returns the User object if authentication is successful, or None if it fails.

        Args:
            api_key (str): The API key provided in the Fever request.

        Returns:
            User | None: The authenticated User object if successful, or None if authentication fails.
        """

        return await self.user_repo.get_by_fever_api_key(api_key)

    async def _handle_login(self, q: FeverQuery, f: FeverForm) -> FeverResponseOut:
        """
        Handle undocumented Fever login requests.

        The login action is performed using `action=login` along with the user's
        email as `username` and the plain password as `password`.
        """

        if not f.username or not f.password:
            return FeverResponseOut(auth=0)

        user = await self.user_repo.get_by(email=f.username)
        if user is None or user.password_salt is None or user.hashed_password is None:
            return FeverResponseOut(auth=0)

        if not get_hasher().verify(f.password, user.password_salt, user.hashed_password):
            return FeverResponseOut(auth=0)

        if not user.fever_key:
            user.fever_key = generate_fever_key(user.email, f.password)
            self.db.add(user)

            await self.db.commit()
            await self.db.refresh(user)

        return FeverResponseOut(auth=1)

    async def _handle_mark(
        self,
        q: FeverQuery,
        user: User,
    ) -> None:
        """
        Handle marking items, feeds, or groups as read/unread/saved/unsaved based on the Fever API request parameters.

        Args:
            q (FeverQuery): The parsed query parameters from the Fever request.
            user (User): The authenticated user making the request.

        Returns:
            None
        """

        if q.mark == "item":
            await self._handle_mark_item(q, user)
        elif q.mark == "feed":
            if q.as_ == "read":
                await self._handle_mark_feed(q, user)
        elif q.mark == "group":
            if q.as_ == "read":
                await self._handle_mark_group(q, user)

    async def _handle_mark_item(self, q: FeverQuery, user: User) -> None:
        article = await self.article_repo.get(UUID(int=q.id))
        if article is None:
            return

        has_access = await self.feed_subscription_repo.exists(user_id=user.id, feed_id=article.feed_id)
        if not has_access:
            return

        status = await self.article_status_repo.get_by(article_id=article.id, user_id=user.id)
        if not status:
            status = await self.article_status_repo.create({"article_id": article.id, "user_id": user.id})

        status_updates: dict[str, bool] = {}
        if q.as_ == "read":
            status_updates["is_read"] = True
        elif q.as_ == "unread":
            status_updates["is_read"] = False
        elif q.as_ == "saved":
            status_updates["is_starred"] = True
        elif q.as_ == "unsaved":
            status_updates["is_starred"] = False

        await self.article_status_repo.update_with_obj(status, status_updates)
        await self.article_status_repo.commit()

    async def _handle_mark_feed(self, q: FeverQuery, user: User) -> None:
        cutoff = datetime.fromtimestamp(q.before, tz=UTC) if q.before else None
        feed_id = UUID(int=q.id)

        article_builder = self.article_repo.query().where(col(Article.feed_id) == feed_id)
        if cutoff:
            article_builder = article_builder.where(col(Article.published_at) <= cutoff)

        articles = await article_builder.all()
        for article in articles:
            status = await self.article_status_repo.get_by(article_id=article.id, user_id=user.id)
            if not status:
                await self.article_status_repo.create({"article_id": article.id, "user_id": user.id, "is_read": True})
                await self.article_status_repo.commit()
            else:
                await self.article_status_repo.update_with_obj(status, {"is_read": True})
                await self.article_status_repo.commit()

    async def _handle_mark_group(self, q: FeverQuery, user: User) -> None:
        cutoff = datetime.fromtimestamp(q.before, tz=UTC) if q.before else None

        feed_builder = self.feed_subscription_repo.query().where(col(FeedSubscription.user_id) == user.id)
        if q.id == 0:
            feed_builder = feed_builder.where(col(FeedSubscription.folder_id).is_(None))
        elif q.id == -1:
            feed_builder = feed_builder.join(Feed, col(FeedSubscription.feed_id) == col(Feed.id)).where(
                col(Feed.is_spark) == True
            )
        else:
            feed_builder = feed_builder.where(col(FeedSubscription.folder_id) == UUID(int=q.id))

        subs = await feed_builder.all()
        feed_ids = [s.feed_id for s in subs]

        if not feed_ids:
            return

        article_builder = self.article_repo.query().where(col(Article.feed_id).in_(feed_ids))
        if cutoff:
            article_builder = article_builder.where(col(Article.published_at) <= cutoff)

        articles = await article_builder.all()
        for article in articles:
            status = await self.article_status_repo.get_by(article_id=article.id, user_id=user.id)
            if not status:
                await self.article_status_repo.create(
                    {
                        "article_id": article.id,
                        "user_id": user.id,
                        "is_read": True,
                    }
                )
            else:
                await self.article_status_repo.update_with_obj(status, {"is_read": True})
                await self.article_status_repo.commit()
