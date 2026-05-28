from unittest.mock import AsyncMock

import pytest

from jobs.article import SendArticleDigestJob
from lib.testing import TestJobCase


class TestSendArticleDigestJob(TestJobCase):

    job_class = SendArticleDigestJob

    async def test_delegates_to_article_digest_service(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.article_digestor.ArticleDigestService"
        ) as MockService:
            MockGetDb.return_value = self.db
            MockService.return_value.run = AsyncMock()

            self.make_job().perform()

        MockGetDb.assert_called_once()
        MockService.assert_called_once_with(self.db)
        MockService.return_value.run.assert_awaited_once()

    async def test_raises_when_service_fails(self):
        with self.patch("bootstrap.database.get_db") as MockGetDb, self.patch(
            "services.article_digestor.ArticleDigestService"
        ) as MockService:
            MockGetDb.return_value = self.db
            MockService.return_value.run = AsyncMock(side_effect=Exception("Digest failed"))

            with pytest.raises(Exception, match="Digest failed"):
                self.make_job().perform()

        MockGetDb.assert_called_once()
        MockService.return_value.run.assert_awaited_once()
