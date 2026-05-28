from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from jobs.article import SweepArticleJob
from lib.testing import TestJobCase


class TestSweepArticleJob(TestJobCase):

    job_class = SweepArticleJob

    async def test_skips_when_sweep_disabled(self):
        with patch("jobs.article.sweep.settings.APP_ARTICLE_SWEEP_ENABLED", False), self.patch(
            "bootstrap.database.get_db"
        ) as MockGetDb:
            self.make_job().perform()

        MockGetDb.assert_not_called()

    async def test_delegates_to_article_repository_when_enabled(self):
        with patch("jobs.article.sweep.settings.APP_ARTICLE_SWEEP_ENABLED", True), self.patch(
            "bootstrap.database.get_db"
        ) as MockGetDb, self.patch("repositories.article.ArticleRepository") as MockArticleRepo:
            MockGetDb.return_value = self.db
            MockArticleRepo.return_value.delete_old_unstarred_unbookmarked_articles = AsyncMock(return_value=5)

            self.make_job().perform()

        MockGetDb.assert_called_once()
        MockArticleRepo.assert_called_once_with(self.db)
        MockArticleRepo.return_value.delete_old_unstarred_unbookmarked_articles.assert_awaited_once()
        deleted_args = MockArticleRepo.return_value.delete_old_unstarred_unbookmarked_articles.call_args[0]
        self.assertEqual(len(deleted_args), 1)
        self.assertIsInstance(deleted_args[0], datetime)

    async def test_raises_when_repository_error_occurs(self):
        with patch("jobs.article.sweep.settings.APP_ARTICLE_SWEEP_ENABLED", True), self.patch(
            "bootstrap.database.get_db"
        ) as MockGetDb, self.patch("repositories.article.ArticleRepository") as MockArticleRepo:
            MockGetDb.return_value = self.db
            MockArticleRepo.return_value.delete_old_unstarred_unbookmarked_articles = AsyncMock(
                side_effect=Exception("Delete failed")
            )

            with pytest.raises(Exception, match="Delete failed"):
                self.make_job().perform()

        MockGetDb.assert_called_once()
        MockArticleRepo.return_value.delete_old_unstarred_unbookmarked_articles.assert_awaited_once()
