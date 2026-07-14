import logging
import os
import unittest
from unittest.mock import patch

from morning_report.privacy import RedactingFilter, redact


class PrivacyTests(unittest.TestCase):
    def test_redacts_known_environment_secret(self):
        secret = "unit-test-secret-value-123456"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}):
            self.assertNotIn(secret, redact(f"request failed for {secret}"))

    def test_redacts_assignment(self):
        self.assertEqual(redact("api_key=not-safe-to-print"), "api_key=[REDACTED]")

    def test_logging_filter_removes_args_after_formatting(self):
        secret = "unit-test-secret-value-123456"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}):
            record = logging.LogRecord("test", logging.INFO, __file__, 1, "failed %s", (secret,), None)
            RedactingFilter().filter(record)
            self.assertNotIn(secret, record.getMessage())


if __name__ == "__main__":
    unittest.main()
