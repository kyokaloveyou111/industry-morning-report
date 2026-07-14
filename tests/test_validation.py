import unittest

from morning_report.models import Article
from morning_report.validation import validate_report


PROFILE = {
    "sections": [
        {"title": "行业速递"},
        {"title": "市场需求"},
    ],
    "minimum_section_chars": 5,
    "minimum_report_chars": 40,
    "maximum_report_chars": 1000,
    "minimum_citations": 2,
}

ARTICLES = [
    Article(title="One", url="https://example.com/one", source="One"),
    Article(title="Two", url="https://example.com/two", source="Two"),
]


class ValidationTests(unittest.TestCase):
    def test_valid_report(self):
        report = """## 行业速递
第一条可靠新闻与分析。[来源：One](https://example.com/one)

## 市场需求
第二条可靠新闻与需求判断。[来源：Two](https://example.com/two)

📌 今日最重要信号来自两项独立事实。
"""
        result = validate_report(report, ARTICLES, PROFILE)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.used_urls, {item.url for item in ARTICLES})

    def test_rejects_invented_url(self):
        report = """## 行业速递
足够长的内容。[来源](https://evil.example/fake)
## 市场需求
足够长的内容。[来源](https://example.com/two)
📌 总结内容。
"""
        result = validate_report(report, ARTICLES, PROFILE)
        self.assertFalse(result.valid)
        self.assertTrue(any("not present" in error for error in result.errors))

    def test_rejects_cross_section_reuse(self):
        report = """## 行业速递
足够长的内容。[来源](https://example.com/one)
## 市场需求
另一段足够长的内容。[来源](https://example.com/one)
📌 总结内容。
"""
        result = validate_report(report, ARTICLES, {**PROFILE, "minimum_citations": 1})
        self.assertTrue(any("reused across sections" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()

