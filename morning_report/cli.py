from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .collector import Collector, deduplicate
from .config import ConfigError, load_profile, load_runtime
from .generator import ReportGenerator
from .lock import RunLock
from .logging_utils import configure_logging
from .models import Article
from .privacy import redact
from .review_metrics import ALLOWED_CATEGORIES, record_review_metrics, review_summary
from .storage import ArticleStore, read_json


def _latest_snapshot(data_dir: Path) -> Path:
    files = sorted((data_dir / "snapshots").glob("materials_*.json"), reverse=True)
    if not files:
        raise RuntimeError("No material snapshot exists; run collect first")
    return files[0]


def _load_snapshot(path: Path) -> list[Article]:
    raw = read_json(path, None)
    if not isinstance(raw, list):
        raise RuntimeError(f"Invalid material snapshot: {path.name}")
    return [Article.from_dict(item) for item in raw if isinstance(item, dict)]


def _prepare(args: argparse.Namespace):
    runtime = load_runtime(args.profile)
    profile = load_profile(runtime.profile_path)
    logger = configure_logging(runtime.log_dir, args.verbose)
    store = ArticleStore(runtime.data_dir)
    return runtime, profile, logger, store


def cmd_collect(args: argparse.Namespace) -> int:
    runtime, profile, logger, store = _prepare(args)
    collector = Collector(profile, store, logger, retries=runtime.max_retries)
    articles = collector.collect()
    logger.info("Collection completed with %d usable materials", len(articles))
    print(json.dumps({"materials": len(articles), "profile": profile["id"]}, ensure_ascii=False))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    runtime, profile, logger, store = _prepare(args)
    snapshot = Path(args.snapshot) if args.snapshot else _latest_snapshot(runtime.data_dir)
    articles = deduplicate([*_load_snapshot(snapshot), *store.load_buffer()])
    articles = articles[: int(profile.get("maximum_prompt_materials", 100))]
    report, validation = ReportGenerator(runtime, profile, store, logger).generate(articles)
    output = ReportGenerator(runtime, profile, store, logger).save(report, validation, len(articles))
    logger.info("Draft saved: %s", output.name)
    print(output)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    runtime, profile, logger, store = _prepare(args)
    with RunLock(runtime.data_dir / ".run.lock"):
        store.set_run_status("running")
        try:
            collector = Collector(profile, store, logger, retries=runtime.max_retries)
            articles = collector.collect()
            articles = articles[: int(profile.get("maximum_prompt_materials", 100))]
            minimum = int(profile.get("minimum_materials", 8))
            if len(articles) < minimum:
                raise RuntimeError(f"Only {len(articles)} materials are available; at least {minimum} are required")
            if args.dry_run:
                store.set_run_status("success", "Dry run completed without an LLM call")
                logger.info("Dry run completed; LLM was not called")
                return 0
            generator = ReportGenerator(runtime, profile, store, logger)
            report, validation = generator.generate(articles)
            output = generator.save(report, validation, len(articles))
            removed = store.cleanup(int(profile.get("snapshot_retention_days", 30)))
            store.set_run_status("success", report=output.name)
            logger.info("Draft saved as %s; removed %d old snapshot(s)", output.name, removed)
            print(output)
        except Exception as exc:
            store.set_run_status("failed", redact(exc))
            raise
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    runtime, profile, logger, store = _prepare(args)
    issues: list[str] = []
    if runtime.api_key_env and not __import__("os").getenv(runtime.api_key_env):
        issues.append(f"Missing environment variable: {runtime.api_key_env}")

    health = read_json(store.health_path, {})
    if isinstance(health, dict):
        for source, state in health.items():
            if int(state.get("consecutive_failures", 0)) >= 3:
                issues.append(f"Source has failed or returned zero items at least 3 times: {source}")

    status = read_json(store.status_path, {})
    if isinstance(status, dict) and status.get("state") == "failed":
        issues.append(f"Most recent scheduled run failed at {status.get('updated_at', 'unknown time')}")

    print(f"Profile: {profile['display_name']} ({profile['id']})")
    print(f"LLM: {runtime.provider}/{runtime.model}")
    print(f"Sources: {len(profile['sources'])}")
    if isinstance(status, dict) and status.get("state"):
        print(f"Last run: {status['state']} at {status.get('updated_at', 'unknown time')}")
    print(f"Privacy: API key values are never displayed")
    quality = review_summary(store.review_metrics_path)
    if quality["reviews"]:
        print(
            f"Human reviews: {quality['reviews']}, average rating {quality['average_rating']}/5, "
            f"draft/final similarity {quality['average_similarity']}"
        )
    if issues:
        for issue in issues:
            logger.warning("Doctor: %s", issue)
        return 1
    print("Doctor: OK")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    runtime, profile, _, store = _prepare(args)
    removed = store.cleanup(args.days or int(profile.get("snapshot_retention_days", 30)))
    print(f"Removed {removed} old snapshot(s)")
    return 0


def cmd_record_review(args: argparse.Namespace) -> int:
    _, _, _, store = _prepare(args)
    metrics = record_review_metrics(
        store.review_metrics_path,
        Path(args.draft),
        Path(args.final),
        args.rating,
        args.category,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print("Only anonymized counts and SHA-256 digests were stored; report text and URLs were not stored.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="morning-report",
        description="Configurable, privacy-safe industry morning report generator",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--profile", help="Path to an industry profile JSON file")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Collect and generate a validated draft")
    run.add_argument("--dry-run", action="store_true", help="Collect without calling an LLM")
    run.set_defaults(func=cmd_run)

    collect = subparsers.add_parser("collect", help="Collect and persist materials")
    collect.set_defaults(func=cmd_collect)

    generate = subparsers.add_parser("generate", help="Generate from saved materials")
    generate.add_argument("--snapshot", help="Optional material snapshot path")
    generate.set_defaults(func=cmd_generate)

    doctor = subparsers.add_parser("doctor", help="Check configuration and source health")
    doctor.set_defaults(func=cmd_doctor)

    cleanup = subparsers.add_parser("cleanup", help="Remove expired material snapshots")
    cleanup.add_argument("--days", type=int, help="Override snapshot retention days")
    cleanup.set_defaults(func=cmd_cleanup)

    record_review = subparsers.add_parser("record-review", help="Store anonymized draft/final review metrics")
    record_review.add_argument("--draft", required=True, help="AI draft Markdown path")
    record_review.add_argument("--final", required=True, help="Human-reviewed Markdown path")
    record_review.add_argument("--rating", type=int, choices=range(1, 6), required=True)
    record_review.add_argument("--category", action="append", choices=sorted(ALLOWED_CATEGORIES), default=[])
    record_review.set_defaults(func=cmd_record_review)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except (ConfigError, RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {redact(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
