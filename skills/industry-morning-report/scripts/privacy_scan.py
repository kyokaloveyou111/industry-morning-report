from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


IGNORED_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
FORBIDDEN_NAMES = {".env", "scraped_cache.json", "buffer.json", "used_urls.json", "source_health.json"}
TEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".txt", ".yaml", ".yml", ".ps1", ".example", ""}

PATTERNS = {
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Anthropic-style secret": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "Authorization header": re.compile(r"(?i)authorization\s*[:=]\s*(?:bearer|token)\s+[A-Za-z0-9._-]{12,}"),
    "Windows user path": re.compile(r"(?i)\b[A-Z]:\\Users\\(?!<|example|username)[^\\\s]+\\"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def candidate_files(root: Path) -> list[Path]:
    command = ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    try:
        completed = subprocess.run(command, capture_output=True, check=True)
        return [root / value.decode("utf-8") for value in completed.stdout.split(b"\0") if value]
    except (FileNotFoundError, subprocess.CalledProcessError, UnicodeDecodeError):
        return [
            path for path in root.rglob("*")
            if path.is_file()
            and not any(part in IGNORED_PARTS | {"data", "logs"} for part in path.relative_to(root).parts)
            and path.name != ".env"
        ]


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in candidate_files(root):
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.name in FORBIDDEN_NAMES or path.name.startswith("morning_report_") or path.name.startswith("materials_"):
            findings.append(f"prohibited generated/private file: {relative}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{relative}:{line_number}: {label}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Find secrets and private artifacts before repository handoff")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings = scan(root)
    if findings:
        print("Privacy scan failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Privacy scan passed: no known secrets or private runtime artifacts found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
