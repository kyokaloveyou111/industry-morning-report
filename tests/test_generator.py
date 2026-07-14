import tempfile
import unittest
from pathlib import Path

from morning_report.config import RuntimeConfig
from morning_report.generator import ReportGenerator
from morning_report.logging_utils import close_logging, configure_logging
from morning_report.models import Article
from morning_report.storage import ArticleStore


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        return next(self.responses)


class GeneratorTests(unittest.TestCase):
    def test_invalid_first_draft_is_retried_and_only_valid_urls_are_marked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = RuntimeConfig(
                profile_path=root / "profile.json",
                data_dir=root / "data",
                log_dir=root / "logs",
                provider="local",
                model="fake",
                api_key_env="",
                base_url=None,
                request_timeout=10,
                max_retries=1,
            )
            profile = {
                "id": "test",
                "display_name": "测试行业",
                "minimum_materials": 2,
                "minimum_citations": 2,
                "minimum_section_chars": 5,
                "minimum_report_chars": 30,
                "maximum_report_chars": 1000,
                "sections": [{"title": "行业速递", "instructions": "写新闻。"}],
            }
            articles = [
                Article(title="One", url="https://example.com/one", source="One"),
                Article(title="Two", url="https://example.com/two", source="Two"),
            ]
            invalid = "## 行业速递\n内容不足且使用假链接 https://fake.example/x\n📌 总结"
            valid = (
                "## 行业速递\n两项独立事实构成今天的主要行业动态。"
                "[来源：One](https://example.com/one) "
                "[来源：Two](https://example.com/two)\n📌 两项事实共同指向稳定需求。"
            )
            client = FakeClient([invalid, valid])
            store = ArticleStore(runtime.data_dir)
            logger = configure_logging(runtime.log_dir)
            generator = ReportGenerator(runtime, profile, store, logger, client)

            report, validation = generator.generate(articles)
            self.assertEqual(client.calls, 2)
            self.assertTrue(validation.valid)
            output = generator.save(report, validation, len(articles))
            self.assertTrue(output.exists())
            self.assertEqual(store.used_urls(), {item.url for item in articles})
            close_logging(logger)


if __name__ == "__main__":
    unittest.main()
