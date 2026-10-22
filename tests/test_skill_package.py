"""Skill package/fixture integrity only; not a score of agent behavior."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/software-stack"
BEHAVIOR = ROOT / "tests/behavior"


class SkillPackageTests(unittest.TestCase):
    def test_local_reference_links_resolve_inside_skill(self):
        for page in SKILL.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                path = (page.parent / target.split("#")[0]).resolve()
                self.assertTrue(path.is_relative_to(SKILL.resolve()), (page, target))
                self.assertTrue(path.is_file(), (page, target))

    def test_behavior_inputs_and_rubrics_are_separate_and_complete(self):
        data = json.loads((BEHAVIOR / "rubric.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        cases = data["cases"]
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for case in cases:
            path = (BEHAVIOR / case["input"]).resolve()
            self.assertTrue(path.is_relative_to((BEHAVIOR / "cases").resolve()))
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 100)
            self.assertTrue(case["criteria"] and case["failures"])
            self.assertTrue(all(isinstance(s, str) and s.strip()
                                for s in case["criteria"] + case["failures"]))

    def test_behavior_guides_use_existing_read_only_topics(self):
        import server
        data = json.loads((BEHAVIOR / "rubric.json").read_text(encoding="utf-8"))
        for case in data["cases"]:
            self.assertTrue(set(case["guides"]).issubset(server.GUIDES))


if __name__ == "__main__":
    unittest.main()
