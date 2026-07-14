import re
import unittest
from pathlib import Path

import morning_report


ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"


class SkillDistributionTests(unittest.TestCase):
    def test_repository_scoped_operator_and_maintainer_exist(self):
        operator = SKILLS / "industry-morning-report" / "SKILL.md"
        maintainer = SKILLS / "industry-morning-report-maintainer" / "SKILL.md"
        self.assertTrue(operator.exists())
        self.assertTrue(maintainer.exists())
        self.assertIn("name: industry-morning-report\n", operator.read_text(encoding="utf-8"))
        self.assertIn("name: industry-morning-report-maintainer\n", maintainer.read_text(encoding="utf-8"))

    def test_skills_locate_project_with_git_not_install_path(self):
        for skill in SKILLS.glob("*/SKILL.md"):
            text = skill.read_text(encoding="utf-8")
            self.assertIn("git rev-parse --show-toplevel", text)
            self.assertNotIn("at `../..`", text)
            self.assertNotIn("python skills/", text)

    def test_skill_versions_match_application(self):
        root_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertEqual(root_version, morning_report.__version__)
        self.assertRegex(project, rf'(?m)^version = "{re.escape(root_version)}"$')
        for skill in SKILLS.glob("*/SKILL.md"):
            self.assertIn(f"Version: {root_version}.", skill.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
