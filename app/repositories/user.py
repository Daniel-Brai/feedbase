from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from lib.database import Repository
from models.user import User


class UserRepository(Repository[User, int]):
    """
    Repository for managing users
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def list_active_users(self) -> list[User]:
        """
        Retrieves a list of active, non-suspended users from the database.

        Returns:
            A list of User objects that are active and not suspended.
        """

        result = (
            await self.query()
            .where(
                col(User.is_active) == True,
                col(User.is_suspended) == False,
            )
            .all()
        )

        return list(result)

    async def get_by_fever_api_key(self, api_key: str) -> User | None:
        """
        Retrieves a user from the database based on their Fever API key.

        Args:
            api_key (str): The Fever API key associated with the user.

        Returns:
            A User object if a matching user is found, otherwise None.
        """

        result = await self.query().where(col(User.fever_key) == api_key).first()
        return result
