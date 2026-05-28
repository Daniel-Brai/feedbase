from uuid import UUID

from fastapi import status
from sqlalchemy.orm import contains_eager
from sqlmodel import col, func
from sqlmodel.ext.asyncio.session import AsyncSession

from filters import FeedFilter
from jobs import FetchFeedJob, RefreshFeedJob
from lib.ext.fastapi import Service, ServiceError
from lib.pagination import CursorPaginationMetadata, CursorParams
from models import Feed, FeedSubscription, Folder, User
from notifiers import PaginationStreamNotification
from repositories import ArticleRepository, FeedRepository, FeedSubscriptionRepository, FolderRepository
from schemas import FeedSubscriptionCreate, FeedSubscriptionFeedOut, FeedSubscriptionOut, FeedSubscriptionUpdate


class FeedSubscriptionService(Service):
    """
    Service for managing feed subscription related operations
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.feed_repo = FeedRepository(db)
        self.article_repo = ArticleRepository(db)
        self.feed_subscription_repo = FeedSubscriptionRepository(db)
        self.folder_repo = FolderRepository(db)

    async def list_subscribed_feeds(
        self,
        user_id: int,
        cursor_params: CursorParams,
        filter_params: FeedFilter | None = None,
    ) -> tuple[str, list[FeedSubscriptionOut], CursorPaginationMetadata]:
        """
        List the feeds that the user is subscribed to, grouped by folder.

        Args:
            user_id (int): The ID of the user whose subscribed feeds are to be listed.
            cursor_params (CursorParams): The cursor pagination parameters for paginating the results.
            filter_params (Filter | None): Optional filter parameters to apply to the query.

        Returns:
            (str, list[FeedFolderOut], CursorPaginationMetadata): A tuple containing a message, a list of feed folders with their respective feeds, and the pagination metadata.
        """

        try:
            query = (
                self.feed_subscription_repo.query()
                .join(Feed, FeedSubscription.feed_id == Feed.id)
                .options(contains_eager(FeedSubscription.feed))  # type: ignore
                .outerjoin(Folder, FeedSubscription.folder_id == Folder.id)
                .options(contains_eager(FeedSubscription.folder))  # type: ignore
                .where(col(FeedSubscription.user_id) == user_id)
                .order_by(
                    func.coalesce(col(Folder.name), "").asc(),
                    func.coalesce(col(FeedSubscription.title), "").asc(),
                    col(FeedSubscription.id).asc(),
                )
            )

            page = await (
                self.feed_subscription_repo.paginate(query=query.stmt)
                .with_params(cursor_params)
                .with_filter(filter_params)
                .with_schema(FeedSubscription)
                .execute_cursor()
            )

            folders_map: dict[UUID | None, FeedSubscriptionOut] = {}

            user_folders = await self.folder_repo.get_user_folders(user_id)
            for folder in user_folders:
                folders_map[folder.id] = FeedSubscriptionOut(
                    id=folder.id,
                    name=folder.name,
                    feeds=[],
                )

            for sub in page.items:
                feed_info = FeedSubscriptionFeedOut(
                    id=sub.id,
                    feed_id=sub.feed.id,
                    name=sub.title or sub.feed.title,
                    status=sub.feed.status,
                    url=sub.feed.url,
                    last_fetched_at=sub.feed.last_fetched_at,
                )

                folder_id = sub.folder.id if sub.folder else None

                if folder_id not in folders_map:
                    folders_map[folder_id] = FeedSubscriptionOut(
                        id=folder_id,
                        name=sub.folder.name if sub.folder else "Uncategorized",
                        feeds=[],
                    )

                folders_map[folder_id].feeds.append(feed_info)

            data = list(folders_map.values())

            data.sort(
                key=lambda folder: (
                    (folder.id is not None),
                    (folder.name or "").lower(),
                )
            )

            for folder in data:
                folder.feeds.sort(key=lambda f: (f.name or "").lower())

            metadata = CursorPaginationMetadata.model_validate(page, from_attributes=True)

            return "Subscriptions retrieved successfully", data, metadata
        except Exception as e:
            self.logger.error(
                "Failed to list subscribed feeds",
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to retrieve subscribed feeds. Please try again later.") from e

    async def subscribe_to_feeds(
        self,
        user_id: int,
        data: FeedSubscriptionCreate,
    ) -> str:
        """
        Subscribe the user to a feed

        Args:
            user_id (int): The ID of the user to subscribe.
            data (FeedSubscriptionCreate): The data required to subscribe to feeds, including the list of feed URLs to subscribe to.

        Returns:
            str: A message indicating the result of the subscription operation.

        Raises:
            ServiceError: If the subscription operation fails, a ServiceError is raised with an appropriate error
        """

        try:
            added = 0
            async with self.transaction():
                for url in data.urls:
                    url_str = str(url)

                    feed = await self.feed_repo.get_by(url=url_str)
                    if not feed:
                        feed = await self.feed_repo.create({"url": url_str, "site_url": None})

                    existing = await self.feed_subscription_repo.get_by(
                        user_id=user_id,
                        feed_id=feed.id,
                    )

                    if existing:
                        continue

                    await self.feed_subscription_repo.create(
                        {
                            "user_id": user_id,
                            "feed_id": feed.id,
                        }
                    )
                    added += 1

                    FetchFeedJob.perform_later(feed_id=feed.id, user_id=user_id)

            if added > 0:
                return f"Feeds subscribed successfully. {added} feed(s) added."

            return "You are already subscribed to the provided feed(s)."

        except Exception as e:
            self.logger.error(
                "Failed to subscribe to feeds",
                user_id=user_id,
                error=str(e),
                exc_info=e,
            )
            raise ServiceError("Failed to subscribe to feeds. Please try again later.") from e

    async def unsubscribe_from_feed(
        self,
        user: User,
        subscription_id: UUID,
    ) -> str:
        """
        Unsubscribe the user from a feed

        Args:
            user (User): The user to unsubscribe.
            subscription_id (UUID): The ID of the subscription to unsubscribe from.

        Returns:
            str: A message indicating the result of the unsubscribe operation.

        Raises:
            ServiceError: If the unsubscribe operation fails, a ServiceError is raised with an appropriate error
        """

        async with self.transaction():
            feed_subscription = await self.feed_subscription_repo.get_by(id=subscription_id, user_id=user.id)

            if not feed_subscription:
                raise ServiceError("Subscription not found.", status_code=status.HTTP_404_NOT_FOUND)

            result = await self.feed_subscription_repo.delete_with_obj(feed_subscription)

            if not result:
                raise ServiceError("Failed to unsubscribe from feed. Please try again later.")
            else:
                await PaginationStreamNotification(dom_id="subscriptions").deliver(user)

        return "Feed unsubscribed successfully."

    async def update_subscription(
        self,
        user_id: int,
        subscription_id: UUID,
        data: FeedSubscriptionUpdate,
    ) -> str:
        """
        Update an existing feed subscription.

        Args:
            user_id (int): The ID of the user who owns the subscription.
            subscription_id (UUID): The ID of the subscription to update.
            data (FeedSubscriptionUpdate): The updated data for the subscription.

        Returns:
            str: A message indicating the result of the update operation.

        Raises:
            ServiceError: If the update operation fails, a ServiceError is raised with an appropriate error message.
        """

        existing_feed_subscription = await self.feed_subscription_repo.get_by(id=subscription_id, user_id=user_id)

        if not existing_feed_subscription:
            raise ServiceError("Subscription not found.", status_code=status.HTTP_404_NOT_FOUND)

        update_data = data.model_dump()

        if "title" in update_data and update_data["title"] is None:
            update_data.pop("title")

        if not update_data:
            return "Subscription updated successfully."

        feed_subscription = await self.feed_subscription_repo.update_with_obj(existing_feed_subscription, update_data)

        await self.feed_subscription_repo.commit()

        if not feed_subscription:
            raise ServiceError("Failed to update subscription. Please try again later.")

        return "Subscription updated successfully."

    async def refresh_subscriptions(
        self,
        user: User,
    ) -> str:
        """
        Refresh all feed subscriptions for the user by fetching the latest articles for each subscribed feed.

        Args:
            user (User): The user whose feed subscriptions are to be refreshed.

        Returns:
            str: A message indicating the result of the refresh operation.
        """

        RefreshFeedJob.perform_later(user_id=user.id)

        return "Feed subscriptions refresh initiated successfully."
