import unittest

from morning_report.collector import deduplicate, normalize_url, title_similarity
from morning_report.models import Article


class CollectorTests(unittest.TestCase):
    def test_normalize_url_removes_fragment(self):
        self.assertEqual(normalize_url("HTTPS://Example.COM/news?a=1#section"), "https://example.com/news?a=1")

    def test_deduplicate_rejects_same_url_and_similar_title(self):
        articles = [
            Article(title="Company launches a new MicroLED display", url="https://example.com/a", source="A"),
            Article(title="Company launches new MicroLED display", url="https://example.org/b", source="B"),
            Article(title="A separate supply chain update", url="https://example.com/c", source="C"),
            Article(title="Duplicate URL", url="https://example.com/c#top", source="D"),
        ]
        result = deduplicate(articles, threshold=0.80)
        self.assertEqual([item.url for item in result], ["https://example.com/a", "https://example.com/c"])

    def test_similarity_is_normalized(self):
        self.assertGreater(title_similarity("【News】Mini-LED update", "News Mini LED update"), 0.9)


if __name__ == "__main__":
    unittest.main()

