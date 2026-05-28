import asyncio
import random

from locust import HttpUser, between, events, task

from bootstrap.auth import configure_auth
from helpers import generate_fever_key
from lib.auth import create_users, delete_users
from lib.auth.security import Hasher
from lib.logger import get_logger
from settings import settings

logger = get_logger(__name__)

Hasher.configure(time_cost=1, memory_cost=1024, parallelism=1)

configure_auth()


USER_COUNT = 5000
LOAD_TEST_PASSWORD = "LoadTestPassword123!"

FEED_URLS = [
    "https://news.ycombinator.com/rss",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
]


@events.init.add_listener
def seed_users(environment, **kwargs):  # noqa: ARG001
    """
    Fires once when Locust initialises, before any users spawn.
    """

    logger.info(f"Seeding {USER_COUNT} load test users...")

    user_dicts = [
        {
            "name": f"Load Test User {i}",
            "email": f"loadtest_{i}@example.com",
            "password": LOAD_TEST_PASSWORD,
            "is_active": True,
            "email_verified": True,
            "roles": [],
            "fever_key": generate_fever_key(f"loadtest_{i}@example.com", LOAD_TEST_PASSWORD),
            "avatar": None,
            "preferences": {
                "digest_frequency": None,
                "digest_hour": None,
                "mark_article_as_unread_if_updated": False,
                "allow_push_notifications": False,
                "last_digest_sent": None,
            },
        }
        for i in range(USER_COUNT)
    ]

    asyncio.run(create_users(user_dicts, raise_exceptions=False))
    logger.info("Seeding complete.")


@events.quitting.add_listener
def cleanup_users(environment, **kwargs):  # noqa: ARG001
    """
    Deletes any seeded load test users after the load test has finished.
    """

    logger.info(f"Deleting {USER_COUNT} load test users...")
    emails = [f"loadtest_{i}@example.com" for i in range(USER_COUNT)]
    deleted_count = asyncio.run(delete_users("email", emails))
    logger.info(f"Deleted {deleted_count} load test users.")


class FeedbaseUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        user_index = random.randint(0, USER_COUNT - 1)
        resp = self.client.post(
            "/api/v1/auth/login",
            name="Login",
            json={
                "email": f"loadtest_{user_index}@example.com",
                "password": LOAD_TEST_PASSWORD,
            },
        )
        if resp.status_code != 200:
            logger.error(f"Login failed for user {user_index}: {resp.text}")
            self.environment.runner.quit()
            return

        if settings.AUTH_SESSION_COOKIE_NAME not in self.client.cookies:
            raise Exception("Auth cookie not set after login")

    @task(5)
    def browse_feed_list(self):
        self.client.get("/api/v1/subscriptions", params={"size": 20}, name="Browse Subscribed Feeds")

    @task(10)
    def browse_articles(self):
        self.client.get("/api/v1/articles", params={"size": 20}, name="Browse Articles")

    def _get_random_article_id(self) -> str | None:
        response = self.client.get("/api/v1/articles", params={"size": 20}, name="List Articles")
        if response.status_code != 200:
            return None

        articles = response.json().get("data") or []
        if not articles:
            return None

        return random.choice(articles).get("id")

    def _update_article_status(self, article_id: str | None, payload: dict[str, bool], name: str) -> None:
        if not article_id:
            return

        self.client.patch(
            f"/api/v1/articles/{article_id}/status",
            json=payload,
            name=name,
        )

    @task(4)
    def read_article(self):
        article_id = self._get_random_article_id()
        self._update_article_status(article_id, {"is_read": True}, "Mark Article Read")

    @task(3)
    def bookmark_article(self):
        article_id = self._get_random_article_id()
        self._update_article_status(article_id, {"is_bookmarked": True}, "Bookmark Article")

    @task(2)
    def star_article(self):
        article_id = self._get_random_article_id()
        self._update_article_status(article_id, {"is_starred": True}, "Star Article")

    @task(2)
    def discover_feed(self):
        self.client.post(
            "/api/v1/feeds/discover",
            json={"url": random.choice(FEED_URLS)},
            name="Discover Feeds",
        )

    @task(1)
    def subscribe_to_feed(self):
        self.client.post(
            "/api/v1/subscriptions",
            json={"urls": [random.choice(FEED_URLS)]},
            name="Subscribe to Feeds",
        )
