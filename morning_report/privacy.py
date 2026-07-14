from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable


SECRET_NAMES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
)


def known_secrets() -> list[str]:
    return [value for name in SECRET_NAMES if (value := os.getenv(name))]


def redact(text: object, extra_secrets: Iterable[str] = ()) -> str:
    result = str(text)
    for secret in [*known_secrets(), *extra_secrets]:
        if secret and len(secret) >= 6:
            result = result.replace(secret, "[REDACTED]")
    result = re.sub(
        r"(?i)(api[_-]?key|auth[_-]?token|access[_-]?token|password)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        result,
    )
    return result


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = ()
        return True

