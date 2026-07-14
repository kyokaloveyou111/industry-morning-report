from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    profile_path: Path
    data_dir: Path
    log_dir: Path
    provider: str
    model: str
    api_key_env: str
    base_url: str | None
    request_timeout: int
    max_retries: int


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Profile not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in profile {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError("Profile root must be a JSON object")
    return value


def load_profile(path: str | Path | None = None) -> dict[str, Any]:
    selected = path or os.getenv("MORNING_REPORT_PROFILE", "profiles/led.json")
    profile_path = Path(selected)
    if not profile_path.is_absolute():
        profile_path = ROOT / profile_path
    profile = _load_json(profile_path)

    required = {"id", "display_name", "keywords", "sections", "sources"}
    missing = sorted(required - profile.keys())
    if missing:
        raise ConfigError(f"Profile is missing required fields: {', '.join(missing)}")
    if not isinstance(profile["sections"], list) or not profile["sections"]:
        raise ConfigError("Profile sections must be a non-empty list")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", str(profile["id"])):
        raise ConfigError("Profile id must contain only lowercase letters, digits, and hyphens")
    if not isinstance(profile["keywords"], list) or not any(str(item).strip() for item in profile["keywords"]):
        raise ConfigError("Profile keywords must be a non-empty list")
    if not isinstance(profile["sources"], list) or not profile["sources"]:
        raise ConfigError("Profile sources must be a non-empty list")

    section_titles: set[str] = set()
    for section in profile["sections"]:
        if not isinstance(section, dict) or not section.get("title") or not section.get("instructions"):
            raise ConfigError("Every section requires title and instructions")
        if section["title"] in section_titles:
            raise ConfigError(f"Duplicate section title: {section['title']}")
        section_titles.add(section["title"])

    for source in profile["sources"]:
        if not isinstance(source, dict) or source.get("type") not in {"rss", "web"}:
            raise ConfigError("Every source requires type rss or web")
        if not source.get("name") or not source.get("url"):
            raise ConfigError("Every source requires name and url")
        parsed = urlparse(source["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ConfigError(f"Source must use a public HTTP(S) URL without embedded credentials: {source['name']}")
        if source["type"] == "web" and not source.get("selector"):
            raise ConfigError(f"Web source requires a CSS selector: {source['name']}")
    return profile


def load_runtime(profile_path: str | Path | None = None) -> RuntimeConfig:
    selected = Path(profile_path or os.getenv("MORNING_REPORT_PROFILE", "profiles/led.json"))
    if not selected.is_absolute():
        selected = ROOT / selected

    provider = os.getenv("MORNING_REPORT_LLM_PROVIDER", "anthropic").lower()
    key_env_by_provider = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "local": "",
    }
    if provider not in key_env_by_provider:
        raise ConfigError(f"Unsupported LLM provider: {provider}")

    base_url = os.getenv(f"{provider.upper()}_BASE_URL") if provider != "local" else os.getenv("OLLAMA_BASE_URL")
    model_default = "claude-sonnet-4-5" if provider == "anthropic" else "gpt-4.1-mini"
    if provider == "local":
        model_default = "qwen2.5:14b"

    return RuntimeConfig(
        profile_path=selected,
        data_dir=ROOT / "data",
        log_dir=ROOT / "logs",
        provider=provider,
        model=os.getenv("MORNING_REPORT_LLM_MODEL", model_default),
        api_key_env=key_env_by_provider[provider],
        base_url=base_url,
        request_timeout=max(10, int(os.getenv("MORNING_REPORT_TIMEOUT", "120"))),
        max_retries=max(0, int(os.getenv("MORNING_REPORT_RETRIES", "2"))),
    )


def require_api_key(runtime: RuntimeConfig) -> str:
    if not runtime.api_key_env:
        return ""
    key = os.getenv(runtime.api_key_env, "").strip()
    if not key:
        raise ConfigError(f"Required environment variable is not set: {runtime.api_key_env}")
    return key
