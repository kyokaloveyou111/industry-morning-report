import json
import tempfile
import unittest
from pathlib import Path

from morning_report.review_metrics import build_review_metrics, record_review_metrics, review_summary


class ReviewMetricsTests(unittest.TestCase):
    def test_metrics_contain_counts_and_hashes_but_not_report_content_or_urls(self):
        draft = "## 行业速递\n敏感草稿文字 [来源](https://example.com/a)"
        final = "## 行业速递\n审核后的文字 [来源](https://example.com/b)"
        metrics = build_review_metrics(draft, final, 4, ["factual", "source"])
        serialized = json.dumps(metrics, ensure_ascii=False)

        self.assertNotIn("敏感草稿文字", serialized)
        self.assertNotIn("审核后的文字", serialized)
        self.assertNotIn("https://", serialized)
        self.assertEqual(metrics["citations_added"], 1)
        self.assertEqual(metrics["citations_removed"], 1)
        self.assertEqual(len(metrics["draft_sha256"]), 64)

    def test_record_and_summarize(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "draft.md"
            final = root / "final.md"
            output = root / "metrics.json"
            draft_text = "private draft sentence"
            final_text = "reviewed final sentence"
            draft.write_text(draft_text, encoding="utf-8")
            final.write_text(final_text, encoding="utf-8")

            record_review_metrics(output, draft, final, 5, ["style"])
            summary = review_summary(output)
            self.assertEqual(summary["reviews"], 1)
            self.assertEqual(summary["average_rating"], 5)
            stored = output.read_text(encoding="utf-8")
            self.assertNotIn(draft_text, stored)
            self.assertNotIn(final_text, stored)

    def test_rejects_unknown_category(self):
        with self.assertRaises(ValueError):
            build_review_metrics("a", "b", 3, ["confidential-note"])


if __name__ == "__main__":
    unittest.main()
