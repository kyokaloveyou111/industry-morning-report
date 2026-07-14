import json
import tempfile
import unittest
from pathlib import Path

from morning_report.config import ConfigError, load_profile


def valid_profile():
    return {
        "id": "test-industry",
        "display_name": "测试行业",
        "keywords": ["test"],
        "sections": [{"title": "行业速递", "instructions": "写行业信息。"}],
        "sources": [{"type": "rss", "name": "Example", "url": "https://example.com/feed.xml"}],
    }


class ConfigTests(unittest.TestCase):
    def write_profile(self, value):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "profile.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return directory, path

    def test_loads_valid_profile(self):
        directory, path = self.write_profile(valid_profile())
        try:
            self.assertEqual(load_profile(path)["id"], "test-industry")
        finally:
            directory.cleanup()

    def test_rejects_embedded_source_credentials(self):
        profile = valid_profile()
        profile["sources"][0]["url"] = "https://user:password@example.com/feed.xml"
        directory, path = self.write_profile(profile)
        try:
            with self.assertRaises(ConfigError):
                load_profile(path)
        finally:
            directory.cleanup()

    def test_rejects_web_source_without_selector(self):
        profile = valid_profile()
        profile["sources"][0]["type"] = "web"
        directory, path = self.write_profile(profile)
        try:
            with self.assertRaises(ConfigError):
                load_profile(path)
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
