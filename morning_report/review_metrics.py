from __future__ import annotations

import difflib
import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .storage import atomic_write_json, read_json


URL_PATTERN = re.compile(r"https?://[^\s)>\]】]+")
HEADING_PATTERN = re.compile(r"(?m)^#{1,6}\s+")
ALLOWED_CATEGORIES = {"factual", "source", "structure", "style", "duplication", "other"}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_review_metrics(
    draft: str,
    final: str,
    rating: int,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    if rating < 1 or rating > 5:
        raise ValueError("rating must be between 1 and 5")
    selected = sorted(set(categories or []))
    invalid = sorted(set(selected) - ALLOWED_CATEGORIES)
    if invalid:
        raise ValueError(f"unsupported review categories: {', '.join(invalid)}")

    draft_urls = set(URL_PATTERN.findall(draft))
    final_urls = set(URL_PATTERN.findall(final))
    similarity = difflib.SequenceMatcher(None, draft, final, autojunk=False).ratio()
    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "rating": rating,
        "categories": selected,
        "draft_sha256": _digest(draft),
        "final_sha256": _digest(final),
        "draft_chars": len(draft),
        "final_chars": len(final),
        "similarity_ratio": round(similarity, 4),
        "draft_headings": len(HEADING_PATTERN.findall(draft)),
        "final_headings": len(HEADING_PATTERN.findall(final)),
        "draft_citations": len(draft_urls),
        "final_citations": len(final_urls),
        "citations_added": len(final_urls - draft_urls),
        "citations_removed": len(draft_urls - final_urls),
    }


def record_review_metrics(
    output_path: Path,
    draft_path: Path,
    final_path: Path,
    rating: int,
    categories: list[str] | None = None,
    max_records: int = 365,
) -> dict[str, Any]:
    draft = draft_path.read_text(encoding="utf-8")
    final = final_path.read_text(encoding="utf-8")
    metrics = build_review_metrics(draft, final, rating, categories)
    raw = read_json(output_path, [])
    records = raw if isinstance(raw, list) else []
    records.append(metrics)
    atomic_write_json(output_path, records[-max_records:])
    return metrics


def review_summary(path: Path) -> dict[str, float | int]:
    raw = read_json(path, [])
    if not isinstance(raw, list) or not raw:
        return {"reviews": 0}
    ratings = [item.get("rating") for item in raw if isinstance(item, dict) and isinstance(item.get("rating"), int)]
    similarities = [
        item.get("similarity_ratio") for item in raw
        if isinstance(item, dict) and isinstance(item.get("similarity_ratio"), (int, float))
    ]
    return {
        "reviews": len(raw),
        "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "average_similarity": round(sum(similarities) / len(similarities), 4) if similarities else 0,
    }
