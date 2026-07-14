from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .models import Article


def utc_now() -> datetime:
    return datetime.now(UTC)


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


class ArticleStore:
    """Persist snapshots and recovery data without hiding articles on retries."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cache_path = data_dir / "article_cache.json"
        self.buffer_path = data_dir / "buffer.json"
        self.used_path = data_dir / "used_urls.json"
        self.health_path = data_dir / "source_health.json"
        self.status_path = data_dir / "last_run_status.json"

    def set_run_status(self, state: str, message: str = "", report: str = "") -> None:
        atomic_write_json(self.status_path, {
            "state": state,
            "updated_at": utc_now().isoformat(),
            "message": message[:500],
            "report": report,
        })

    def save_snapshot(self, articles: list[Article]) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.data_dir / "snapshots" / f"materials_{timestamp}.json"
        atomic_write_json(path, [article.to_dict() for article in articles])
        return path

    def update_cache(self, articles: list[Article], retention_days: int = 7) -> None:
        now = utc_now().isoformat()
        cutoff = utc_now() - timedelta(days=retention_days)
        raw = read_json(self.cache_path, {})
        cache = raw if isinstance(raw, dict) else {}

        for article in articles:
            previous = cache.get(article.url, {})
            cache[article.url] = {
                "first_seen": previous.get("first_seen", now),
                "last_seen": now,
                "article": article.to_dict(),
            }

        cleaned: dict[str, Any] = {}
        for url, entry in cache.items():
            try:
                last_seen = datetime.fromisoformat(entry["last_seen"])
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=UTC)
                if last_seen >= cutoff:
                    cleaned[url] = entry
            except (KeyError, TypeError, ValueError):
                continue
        atomic_write_json(self.cache_path, cleaned)

    def recovery_articles(self, max_age_hours: int = 36) -> list[Article]:
        cutoff = utc_now() - timedelta(hours=max_age_hours)
        cache = read_json(self.cache_path, {})
        recovered: list[Article] = []
        if not isinstance(cache, dict):
            return recovered
        for entry in cache.values():
            try:
                last_seen = datetime.fromisoformat(entry["last_seen"])
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=UTC)
                if last_seen >= cutoff:
                    recovered.append(Article.from_dict(entry["article"]))
            except (KeyError, TypeError, ValueError):
                continue
        return recovered

    def save_buffer(self, articles: list[Article], retention_hours: int = 48) -> None:
        """Save on every collection attempt so generation failures remain recoverable."""
        now = utc_now().isoformat()
        cutoff = utc_now() - timedelta(hours=retention_hours)
        raw = read_json(self.buffer_path, [])
        by_url: dict[str, dict[str, Any]] = {}
        if isinstance(raw, list):
            for entry in raw:
                try:
                    buffered_at = datetime.fromisoformat(entry["buffered_at"])
                    if buffered_at.tzinfo is None:
                        buffered_at = buffered_at.replace(tzinfo=UTC)
                    if buffered_at >= cutoff:
                        by_url[entry["article"]["url"]] = entry
                except (KeyError, TypeError, ValueError):
                    continue
        for article in articles:
            by_url[article.url] = {"buffered_at": now, "article": article.to_dict()}
        atomic_write_json(self.buffer_path, list(by_url.values()))

    def load_buffer(self, max_age_hours: int = 48) -> list[Article]:
        cutoff = utc_now() - timedelta(hours=max_age_hours)
        raw = read_json(self.buffer_path, [])
        articles: list[Article] = []
        if not isinstance(raw, list):
            return articles
        for entry in raw:
            try:
                buffered_at = datetime.fromisoformat(entry["buffered_at"])
                if buffered_at.tzinfo is None:
                    buffered_at = buffered_at.replace(tzinfo=UTC)
                if buffered_at >= cutoff:
                    articles.append(Article.from_dict(entry["article"]))
            except (KeyError, TypeError, ValueError):
                continue
        return articles

    def used_urls(self, retention_days: int = 7) -> set[str]:
        cutoff = (utc_now() - timedelta(days=retention_days)).date().isoformat()
        raw = read_json(self.used_path, {})
        if not isinstance(raw, dict):
            return set()
        return {url for url, used_on in raw.items() if isinstance(used_on, str) and used_on >= cutoff}

    def mark_used(self, urls: set[str], retention_days: int = 7) -> None:
        today = utc_now().date().isoformat()
        cutoff = (utc_now() - timedelta(days=retention_days)).date().isoformat()
        raw = read_json(self.used_path, {})
        used = raw if isinstance(raw, dict) else {}
        used.update({url: today for url in urls})
        atomic_write_json(
            self.used_path,
            {url: date for url, date in used.items() if isinstance(date, str) and date >= cutoff},
        )

    def update_source_health(self, name: str, ok: bool, item_count: int, error: str = "") -> None:
        health = read_json(self.health_path, {})
        if not isinstance(health, dict):
            health = {}
        previous = health.get(name, {})
        consecutive_failures = 0 if ok and item_count > 0 else int(previous.get("consecutive_failures", 0)) + 1
        health[name] = {
            "checked_at": utc_now().isoformat(),
            "ok": ok,
            "item_count": item_count,
            "consecutive_failures": consecutive_failures,
            "last_success_at": utc_now().isoformat() if ok and item_count > 0 else previous.get("last_success_at"),
            "error": error[:300],
        }
        atomic_write_json(self.health_path, health)

    def cleanup(self, retention_days: int = 30) -> int:
        cutoff = utc_now() - timedelta(days=retention_days)
        removed = 0
        snapshot_dir = self.data_dir / "snapshots"
        if snapshot_dir.exists():
            for path in snapshot_dir.glob("materials_*.json"):
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
                if modified < cutoff:
                    path.unlink()
                    removed += 1
        return removed
