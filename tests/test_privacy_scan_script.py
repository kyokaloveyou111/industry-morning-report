import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".agents" / "skills" / "industry-morning-report-maintainer" / "scripts" / "privacy_scan.py"
SPEC = importlib.util.spec_from_file_location("privacy_scan_v2", SCRIPT)
privacy_scan = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = privacy_scan
SPEC.loader.exec_module(privacy_scan)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class PrivacyScanScriptTests(unittest.TestCase):
    def make_repo(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        git(root, "init", "-b", "main")
        git(root, "config", "user.name", "Test User")
        git(root, "config", "user.email", "test@example.invalid")
        return temporary, root

    def test_reads_exact_staged_content_not_overwritten_worktree(self):
        temporary, root = self.make_repo()
        try:
            path = root / "config.txt"
            path.write_text("safe\n", encoding="utf-8")
            git(root, "add", "config.txt")
            git(root, "commit", "-m", "safe")

            synthetic_value = "sk-" + "A" * 32
            path.write_text(f"api_key={synthetic_value}\n", encoding="utf-8")
            git(root, "add", "config.txt")
            path.write_text("safe again\n", encoding="utf-8")

            findings = privacy_scan.scan_publishable(root)
            self.assertTrue(any(item.location == "index:config.txt" for item in findings))
            self.assertTrue(any("secret" in item.label.lower() or "credential" in item.label.lower() for item in findings))
        finally:
            temporary.cleanup()

    def test_history_scan_finds_removed_secret(self):
        temporary, root = self.make_repo()
        try:
            path = root / "old.txt"
            synthetic_value = "ghp_" + "B" * 32
            path.write_text(synthetic_value, encoding="utf-8")
            git(root, "add", "old.txt")
            git(root, "commit", "-m", "old")
            path.unlink()
            git(root, "add", "--all")
            git(root, "commit", "-m", "remove")

            findings = privacy_scan.scan_history(root)
            self.assertTrue(any(item.label == "GitHub token" for item in findings))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
