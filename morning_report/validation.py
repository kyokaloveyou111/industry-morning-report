from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .models import Article


URL_PATTERN = re.compile(r"https?://[^\s)>\]】]+")
HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


@dataclass(slots=True)
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    used_urls: set[str] = field(default_factory=set)

    @property
    def valid(self) -> bool:
        return not self.errors


def _split_sections(report: str) -> dict[str, str]:
    matches = list(HEADING_PATTERN.finditer(report))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(report)
        result[match.group(1).strip()] = report[match.end():end]
    return result


def validate_report(report: str, articles: list[Article], profile: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    allowed_urls = {article.url for article in articles}
    report_urls = {url.rstrip(".,，。") for url in URL_PATTERN.findall(report)}
    result.used_urls = report_urls & allowed_urls

    invented = sorted(report_urls - allowed_urls)
    if invented:
        result.errors.append(f"Report contains {len(invented)} URL(s) not present in the supplied materials")

    sections = _split_sections(report)
    expected_titles = [section["title"] for section in profile["sections"]]
    for title in expected_titles:
        if title not in sections:
            result.errors.append(f"Missing required section: {title}")
        elif len(re.sub(r"\s+", "", sections[title])) < int(profile.get("minimum_section_chars", 40)):
            result.errors.append(f"Section is too short: {title}")

    url_owner: dict[str, str] = {}
    for title, body in sections.items():
        for url in set(URL_PATTERN.findall(body)):
            url = url.rstrip(".,，。")
            if url in url_owner and url_owner[url] != title:
                result.errors.append(f"The same source URL is reused across sections: {url}")
            url_owner[url] = title

    char_count = len(re.sub(r"\s+", "", report))
    minimum = int(profile.get("minimum_report_chars", 500))
    maximum = int(profile.get("maximum_report_chars", 2500))
    if char_count < minimum or char_count > maximum:
        result.errors.append(f"Report length {char_count} is outside the allowed range {minimum}-{maximum}")

    if len(result.used_urls) < int(profile.get("minimum_citations", 3)):
        result.errors.append("Report does not cite enough supplied source URLs")

    if not re.search(r"(?m)^📌", report):
        result.errors.append("Missing final key-signal line beginning with 📌")
    return result

