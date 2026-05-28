from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from lib.ext.fastapi import IORunnableService
from lib.mailer.exceptions import MailerNotConfiguredError
from models import User
from repositories import ArticleRepository, UserRepository


class ArticleDigestService(IORunnableService):
    """
    Service for sending email digests to users based on their preferences
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

        self.user_repo = UserRepository(db)
        self.article_repo = ArticleRepository(db)

    async def run(self) -> None:
        """
        Main entry point for the article digest sending process.
        """

        if not self._is_mailer_configured():
            self.logger.warning("Mailer not configured, article digest job aborted")
            return

        now_utc = datetime.now(UTC)
        current_hour = now_utc.hour

        users = await self._get_users_with_digest_preferences()
        if not users:
            self.logger.debug("No users with digest preferences found.")
            return

        for user in users:
            async with self.db.begin_nested():
                try:
                    await self._process_user(user, now_utc, current_hour)
                except Exception:
                    self.logger.exception(f"Failed to process digest for user {user.email}")

        await self.db.commit()

    def _is_mailer_configured(self) -> bool:
        try:
            from lib.mailer import get_mailer

            get_mailer()
            return True
        except MailerNotConfiguredError:
            return False

    async def _get_users_with_digest_preferences(self) -> list[User]:
        users = await self.user_repo.list_active_users()
        return [u for u in users if u.preferences and u.preferences.get("digest_frequency") in ("daily", "weekly")]

    async def _process_user(self, user: User, now_utc: datetime, current_hour: int) -> None:
        prefs = dict(user.preferences or {})
        freq = prefs.get("digest_frequency")
        digest_hour: Any | None = prefs.get("digest_hour")

        if digest_hour is None or digest_hour != current_hour:
            return

        last_sent = prefs.get("last_digest_sent")
        if last_sent:
            last_sent_dt = datetime.fromisoformat(last_sent)
            if freq == "daily" and (now_utc - last_sent_dt) < timedelta(hours=23):
                return
            if freq == "weekly" and (now_utc - last_sent_dt) < timedelta(days=6, hours=23):
                return

        if freq == "daily":
            cutoff = now_utc - timedelta(days=1)
        else:
            cutoff = now_utc - timedelta(days=7)

        articles = await self.article_repo.fetch_unread_articles(user.id, cutoff, now_utc)
        if not articles:
            self.logger.info(f"No new articles for user {user.email}")
            return

        articles_by_feed_id = defaultdict(list)
        for art in articles:
            articles_by_feed_id[art.feed_id].append(art)

        feed_groups = []
        for arts in articles_by_feed_id.values():
            feed = arts[0].feed
            feed_groups.append(
                {
                    "feed_title": feed.title or feed.url,
                    "articles": [
                        {
                            "title": a.title or "Untitled",
                            "url": a.url,
                            "summary": a.summary,
                            "published_at": a.published_at,
                        }
                        for a in arts
                    ],
                }
            )

        from lib.mailer import get_mailer

        mailer = get_mailer()
        await mailer.send_template(
            to=user.email,
            subject=f"Your {freq} digest from Feedbase",
            template="email_digest.mjml.html",
            context={
                "name": user.get_display_name(),
                "frequency": freq,
                "period_start": cutoff,
                "period_end": now_utc,
                "feeds": feed_groups,
            },
        )

        prefs["last_digest_sent"] = now_utc.isoformat()
        user.preferences = prefs
        self.db.add(user)
        self.logger.info(f"Digest sent to {user.email} ({freq})")
