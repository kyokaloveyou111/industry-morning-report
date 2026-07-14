from __future__ import annotations

import difflib
import logging
import random
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import feedparser
import requests
from bs4 import BeautifulSoup

from .models import Article
from .privacy import redact
from .storage import ArticleStore


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/132 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 Version/18 Safari/605.1.15",
]


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", parsed.query, ""))


def normalized_title(title: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", title).lower()


def title_similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalized_title(left), normalized_title(right)).ratio()


def deduplicate(articles: list[Article], threshold: float = 0.82) -> list[Article]:
    result: list[Article] = []
    urls: set[str] = set()
    for article in articles:
        article.url = normalize_url(article.url)
        if not article.url or article.url in urls:
            continue
        if any(title_similarity(article.title, kept.title) >= threshold for kept in result):
            continue
        urls.add(article.url)
        result.append(article)
    return result


def matches_profile(text: str, keywords: list[str]) -> bool:
    haystack = text.casefold()
    return any(keyword.casefold() in haystack for keyword in keywords if keyword.strip())


class Collector:
    def __init__(
        self,
        profile: dict[str, Any],
        store: ArticleStore,
        logger: logging.Logger,
        timeout: int = 20,
        retries: int = 2,
    ):
        self.profile = profile
        self.store = store
        self.logger = logger
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def _get(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7"},
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 4))
        raise RuntimeError(redact(last_error or "request failed"))

    def _classify(self, article: Article) -> None:
        text = f"{article.title} {article.summary}"
        for rule in self.profile.get("category_rules", []):
            if matches_profile(text, rule.get("keywords", [])):
                article.category = rule["category"]
                article.tags = sorted(set([*article.tags, *rule.get("tags", [])]))
                return

    def _rss(self, source: dict[str, Any]) -> list[Article]:
        parsed = feedparser.parse(self._get(source["url"]))
        results: list[Article] = []
        for entry in parsed.entries[: int(source.get("max_items", 30))]:
            title = BeautifulSoup(entry.get("title", ""), "html.parser").get_text(" ", strip=True)
            summary = BeautifulSoup(entry.get("summary", entry.get("description", "")), "html.parser").get_text(" ", strip=True)
            if not title or not matches_profile(f"{title} {summary}", self.profile["keywords"]):
                continue
            article = Article(
                title=title[:180],
                url=entry.get("link", ""),
                source=entry.get("source", {}).get("title", source["name"]),
                category=source.get("category", "industry"),
                summary=summary[:500],
                published_at=entry.get("published", entry.get("updated", "")),
                collected_at=datetime.now(UTC).isoformat(),
            )
            self._classify(article)
            results.append(article)
        return results

    def _web(self, source: dict[str, Any]) -> list[Article]:
        soup = BeautifulSoup(self._get(source["url"]), "html.parser")
        nodes = soup.select(source["selector"])
        results: list[Article] = []
        for node in nodes[: int(source.get("max_items", 30))]:
            link = node if node.name == "a" else node.find("a", href=True)
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            if len(title) < 8 or not matches_profile(title, self.profile["keywords"]):
                continue
            article = Article(
                title=title[:180],
                url=urljoin(source["url"], link.get("href", "")),
                source=source["name"],
                category=source.get("category", "industry"),
                collected_at=datetime.now(UTC).isoformat(),
            )
            self._classify(article)
            results.append(article)
        return results

    def collect(self) -> list[Article]:
        collected: list[Article] = []
        for source in self.profile["sources"]:
            name = source.get("name", "unnamed")
            try:
                if source["type"] == "rss":
                    items = self._rss(source)
                elif source["type"] == "web":
                    items = self._web(source)
                else:
                    raise ValueError(f"Unsupported source type: {source.get('type')}")
                collected.extend(items)
                self.store.update_source_health(name, True, len(items))
                self.logger.info("Source %s produced %d relevant items", name, len(items))
            except Exception as exc:
                safe_error = redact(exc)
                self.store.update_source_health(name, False, 0, safe_error)
                self.logger.warning("Source %s failed: %s", name, safe_error)

        unique = deduplicate(collected)
        self.store.update_cache(unique)
        self.store.save_buffer(unique)
        self.store.save_snapshot(unique)

        minimum = int(self.profile.get("minimum_materials", 8))
        if len(unique) < minimum:
            recovered = deduplicate([*unique, *self.store.load_buffer(), *self.store.recovery_articles()])
            self.logger.warning("Only %d new items; recovery pool provides %d items", len(unique), len(recovered))
            return recovered
        return unique

