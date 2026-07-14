from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new industry profile skeleton")
    parser.add_argument("profile_id", help="Lowercase letters, digits, and hyphens")
    parser.add_argument("display_name")
    parser.add_argument("--keyword", action="append", required=True, dest="keywords")
    parser.add_argument("--output-dir", default="profiles")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", args.profile_id):
        parser.error("profile_id must use lowercase letters, digits, and hyphens")

    path = Path(args.output_dir) / f"{args.profile_id}.json"
    if path.exists():
        parser.error(f"refusing to overwrite existing profile: {path}")

    profile = {
        "id": args.profile_id,
        "display_name": args.display_name,
        "keywords": args.keywords,
        "minimum_materials": 8,
        "maximum_prompt_materials": 80,
        "minimum_citations": 3,
        "minimum_section_chars": 40,
        "minimum_report_chars": 500,
        "maximum_report_chars": 2000,
        "used_url_retention_days": 7,
        "snapshot_retention_days": 30,
        "sections": [
            {"title": "行业速递", "instructions": "选择最重要的行业动态并附来源链接。"},
            {"title": "市场与需求", "instructions": "基于素材分析需求变化。"},
            {"title": "技术与产品", "instructions": "讨论有事实依据的技术或产品变化。"},
            {"title": "供应链与政策", "instructions": "提取供应链、价格、认证或政策变化。"},
        ],
        "category_rules": [],
        "sources": [{
            "type": "rss",
            "name": "REPLACE WITH A PUBLIC SOURCE",
            "url": "https://example.com/feed.xml",
            "max_items": 30,
            "category": "industry",
        }],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {path}. Replace the placeholder source before running collection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
