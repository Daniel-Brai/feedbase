from typing import Any

from httpx import AsyncClient

from settings import settings


async def create_verified_user(
    password: str = "Password1!",
    **user_kwargs: Any,
) -> tuple[Any, str]:
    """
    Helper to create a verified user with the given password.

    Args:
        password (Password): The plaintext password for the user. Defaults to "Password1!".
        **user_kwargs: Optional overrides for the created user object.

    Returns:
        tuple[Any, Password]: A tuple containing the created user object and the plaintext password.
    """

    from lib.auth.security import Hasher
    from lib.auth.user import generate_salt
    from tests.factories import UserFactory

    password_salt = generate_salt()
    hashed_password = Hasher.hash(password, password_salt)

    user = await UserFactory.create(
        email_verified=True,
        password_salt=password_salt,
        hashed_password=hashed_password,
        **user_kwargs,
    )

    return user, password


async def get_auth_token(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    """
    Helper to retrieve the authentication token from the cookies after logging in.

    Args:
        client (AsyncClient): The HTTP client to use for making the login request.
        email (str): The email of the user to log in.
        password (Password): The password of the user to log in.

    Returns:
        dict[str, str]: A dictionary containing the authentication token to be passed in the `cookies` parameter of subsequent requests.
    """

    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password},
    )

    if response.status_code != 200:
        raise ValueError(
            f"Failed to log in with credentials. Status code: {response.status_code}, Response body: {response.text}"
        )

    cookie_name = settings.AUTH_SESSION_COOKIE_NAME
    if cookie_name not in response.cookies:
        raise ValueError(f"Authentication cookie '{cookie_name}' not found in response.")

    return {cookie_name: response.cookies[cookie_name]}


def mount_auth_routes(app) -> None:
    """
    Mount the authentication routes on the given FastAPI app.

    Args:
        app: The FastAPI app to mount the authentication routes on.
    """

    from lib.auth import get_auth_router, get_backend, make_auth_dependency

    auth_dep = make_auth_dependency(get_backend())
    app.include_router(get_auth_router(auth_dep=auth_dep))
