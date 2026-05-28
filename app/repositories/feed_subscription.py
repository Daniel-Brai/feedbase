from uuid import UUID

from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from lib.database import Repository
from models import Feed, FeedSubscription


class FeedSubscriptionRepository(Repository[FeedSubscription, UUID]):
    """
    Repository for managing feed subscriptions
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(FeedSubscription, db)

    async def clear_folder(self, user_id: int, folder_id: UUID) -> None:
        """
        Remove the folder association from all subscriptions for a given user and folder.

        Args:
            user_id (int): The ID of the user whose subscriptions are to be updated.
            folder_id (UUID): The ID of the folder to clear from the subscriptions.

        Returns:
            None
        """

        subs = await self.query().filter_by(user_id=user_id, folder_id=folder_id).all()
        if subs:
            ids = [sub.id for sub in subs]
            data_list = [{"folder_id": None} for _ in ids]
            await self.bulk_update(ids, data_list)

    async def get_user_feeds(self, user_id: int) -> list[Feed]:
        """
        Get the list of feeds that a user is subscribed to.

        Args:
            user_id (int): The ID of the user whose subscribed feeds are to be retrieved.

        Returns:
            list[Feed]: A list of Feed objects that the user is subscribed to.
        """
        results = (
            await self.query().where(col(FeedSubscription.user_id) == user_id).joinload(FeedSubscription.feed).all()
        )
        return [sub.feed for sub in results if sub.feed]

    async def get_fever_user_feed_groups(self, user_id: int) -> dict[int, list[int]]:
        """
        Get a mapping of feed groups to the feeds within each group for a given user.

        Args:
            user_id (int): The ID of the user whose feed groups are to be retrieved.

        Returns:
            dict[int, list[int]]: A dictionary mapping feed group IDs to lists of feed IDs.
        """

        results = await self.query().where(col(FeedSubscription.user_id) == user_id).all()
        mapping: dict[int, list[int]] = {}
        for sub in results:
            gid = sub.folder_id.int if sub.folder_id else 0
            mapping.setdefault(gid, []).append(sub.feed_id.int)

        return mapping
