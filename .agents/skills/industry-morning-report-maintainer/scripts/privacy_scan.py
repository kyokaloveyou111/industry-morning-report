from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


IGNORED_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
FORBIDDEN_NAMES = {
    ".env", "scraped_cache.json", "article_cache.json", "buffer.json",
    "used_urls.json", "source_health.json", "last_run_status.json",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".json", ".toml", ".txt", ".yaml", ".yml", ".ps1",
    ".example", ".cfg", ".ini", ".xml", ".csv", "",
}
MAX_DEFAULT_BYTES = 1_000_000

PATTERNS = {
    "Anthropic-style secret": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{15,}\b"),
    "Stripe live key": re.compile(r"\b[rs]k_live_[A-Za-z0-9]{16,}\b"),
    "Authorization header": re.compile(
        r"(?i)authorization\s*[:=]\s*(?:bearer|token|basic)\s+[A-Za-z0-9._~+/=-]{12,}"
    ),
    "Credential-bearing URL": re.compile(
        r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s/:]+:[^\s/@]+@"
    ),
    "Windows user path": re.compile(r"(?i)\b[A-Z]:\\Users\\(?!<|example|username)[^\\\s]+\\"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
GENERIC_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|auth[_-]?token|access[_-]?token|client[_-]?secret|password)"
    r"\s*[:=]\s*[\"']?([A-Za-z0-9_./+~=-]{20,})"
)
PLACEHOLDER_WORDS = {"replace", "example", "dummy", "placeholder", "your", "changeme", "test"}


@dataclass(frozen=True, slots=True)
class Finding:
    location: str
    line: int
    label: str

    def render(self) -> str:
        return f"{self.location}:{self.line}: {self.label}"


def _git(root: Path, *args: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=check
    )
    return completed.stdout


def _is_git_repository(root: Path) -> bool:
    try:
        return _git(root, "rev-parse", "--is-inside-work-tree").strip() == b"true"
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _publishable_paths(root: Path) -> tuple[list[Path], set[str]]:
    output = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    paths = [Path(value.decode("utf-8")) for value in output.split(b"\0") if value]
    staged_output = _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    staged = {value.decode("utf-8").replace("\\", "/") for value in staged_output.split(b"\0") if value}
    return paths, staged


def _fallback_paths(root: Path) -> list[Path]:
    return [
        path.relative_to(root) for path in root.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS | {"data", "logs"} for part in path.relative_to(root).parts)
        and path.name != ".env"
    ]


def _is_forbidden_path(relative: Path) -> bool:
    return (
        relative.name in FORBIDDEN_NAMES
        or relative.name.startswith("morning_report_")
        or relative.name.startswith("materials_")
        or any(part in {"data", "logs"} for part in relative.parts)
    )


def _scan_text(location: str, payload: bytes) -> list[Finding]:
    if b"\0" in payload:
        return []
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append(Finding(location, line_number, label))
        for match in GENERIC_ASSIGNMENT.finditer(line):
            candidate = match.group(2).casefold()
            if not any(word in candidate for word in PLACEHOLDER_WORDS):
                findings.append(Finding(location, line_number, "Generic credential assignment"))
    return findings


def scan_publishable(root: Path, max_bytes: int = MAX_DEFAULT_BYTES) -> list[Finding]:
    findings: list[Finding] = []
    is_git = _is_git_repository(root)
    if is_git:
        paths, staged = _publishable_paths(root)
    else:
        paths, staged = _fallback_paths(root), set()

    for relative in paths:
        normalized = relative.as_posix()
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if _is_forbidden_path(relative):
            findings.append(Finding(normalized, 0, "Prohibited generated/private file"))
            continue
        if relative.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if is_git and normalized in staged:
                payload = _git(root, "show", f":{normalized}")
                location = f"index:{normalized}"
            else:
                path = root / relative
                if path.stat().st_size > max_bytes:
                    continue
                payload = path.read_bytes()
                location = normalized
        except (FileNotFoundError, OSError, subprocess.CalledProcessError):
            continue
        if len(payload) <= max_bytes:
            findings.extend(_scan_text(location, payload))
    return findings


def scan_history(root: Path, max_bytes: int = MAX_DEFAULT_BYTES) -> list[Finding]:
    if not _is_git_repository(root):
        return []
    findings: list[Finding] = []
    seen: set[str] = set()
    for raw_line in _git(root, "rev-list", "--objects", "--all").splitlines():
        parts = raw_line.decode("utf-8", errors="replace").split(" ", 1)
        object_id = parts[0]
        path = parts[1] if len(parts) == 2 else "<no-path>"
        if object_id in seen:
            continue
        seen.add(object_id)
        try:
            if _git(root, "cat-file", "-t", object_id).strip() != b"blob":
                continue
            size = int(_git(root, "cat-file", "-s", object_id).strip())
            if size > max_bytes:
                continue
            payload = _git(root, "cat-file", "-p", object_id)
        except (ValueError, subprocess.CalledProcessError):
            continue
        findings.extend(_scan_text(f"history:{object_id[:12]}:{path}", payload))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan publishable files, the Git index, and optional history")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--history", action="store_true", help="scan every reachable Git blob")
    parser.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES)
    args = parser.parse_args()
    root = Path(args.root).resolve()

    findings = scan_publishable(root, args.max_bytes)
    if args.history:
        findings.extend(scan_history(root, args.max_bytes))
    unique = sorted({finding.render() for finding in findings})
    if unique:
        print("Privacy scan failed:")
        for finding in unique:
            print(f"- {finding}")
        return 1
    scope = "publishable files, Git index, and history" if args.history else "publishable files and Git index"
    print(f"Privacy scan passed for {scope}; no recognized secrets or private artifacts found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
