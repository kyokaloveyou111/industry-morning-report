import tempfile
import unittest
from pathlib import Path

from morning_report.models import Article
from morning_report.storage import ArticleStore, read_json


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = ArticleStore(Path(self.temporary.name))
        self.article = Article(
            title="Test industry article",
            url="https://example.com/article",
            source="Example",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_failed_generation_material_remains_in_buffer(self):
        self.store.save_buffer([self.article])
        recovered = self.store.load_buffer()
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].url, self.article.url)

    def test_cache_is_recovery_store_not_one_time_filter(self):
        self.store.update_cache([self.article])
        first = self.store.recovery_articles()
        second = self.store.recovery_articles()
        self.assertEqual([item.url for item in first], [self.article.url])
        self.assertEqual([item.url for item in second], [self.article.url])

    def test_used_urls_expire_separately_from_collection_cache(self):
        self.store.mark_used({self.article.url})
        self.assertIn(self.article.url, self.store.used_urls())
        self.assertEqual(read_json(self.store.used_path, {})[self.article.url][:2], "20")

    def test_run_status_is_machine_readable(self):
        self.store.set_run_status("failed", "safe diagnostic")
        status = read_json(self.store.status_path, {})
        self.assertEqual(status["state"], "failed")
        self.assertEqual(status["message"], "safe diagnostic")


if __name__ == "__main__":
    unittest.main()
