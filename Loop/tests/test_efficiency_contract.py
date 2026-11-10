"""Static policy wiring checks, not evidence of real agent compliance or savings."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EfficiencyContract(unittest.TestCase):
    def test_entry_points_reference_companion(self):
        for name in ("loop.md", "DELIVERY-WORKFLOW.md", "MODEL-ROUTING.md", "skills/loop/SKILL.md"):
            with self.subTest(name=name):
                self.assertIn("EFFICIENT-WORKFLOW.md", (ROOT / name).read_text())
        # Every project created by the starter routes sessions to the companion.
        self.assertIn("Loop/EFFICIENT-WORKFLOW.md", (ROOT / "starter" / "templates" / "AGENTS.md").read_text())

    def test_atlas_first_is_wired_into_policy_and_starter(self):
        policy = (ROOT / "loop.md").read_text()
        for name in ("ATLAS-FIRST.md", "OWNER-COMMUNICATION.md", "loop-init.mjs", "CURRENT RESUME"):
            with self.subTest(name=name):
                self.assertIn(name, policy)
        skill = (ROOT / "skills" / "loop" / "SKILL.md").read_text()
        self.assertIn("loop-init.mjs", skill)
        self.assertIn("ATLAS-FIRST.md", skill)
        for path in ("scripts/loop-init.mjs", "starter/docs/app-map/build-atlas.mjs", "starter/docs/app-map/atlas-status.mjs",
                     "starter/docs/app-map/verify-atlas.mjs", "starter/docs/app-map/atlas-template.html", "starter/docs/app-map/atlas-contract.test.mjs",
                     "starter/platforms.mjs", "start/START.md", "start/template-page/README.md", "examples/brief.example.json", "examples/brief.android.example.json", "archive/v0.3.1/loop.md"):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).exists())

    def test_platform_is_chosen_not_assumed(self):
        policy = (ROOT / "loop.md").read_text()
        skill = (ROOT / "skills" / "loop" / "SKILL.md").read_text()
        for text in (policy, skill):
            self.assertIn("which platform", text)
            self.assertNotIn("npm run", text.replace("`npm run atlas*`", ""))
        self.assertIn("platform.md", policy)
        self.assertIn("Never pick the platform for the owner", policy)

    def test_legal_checklist_is_wired_in(self):
        rules = (ROOT / "LEGAL-CHECKLIST.md").read_text()
        for n in range(1, 21):
            with self.subTest(check=n):
                self.assertIn(f"{n}. **", rules)
        self.assertIn("never says the product is \"legally compliant\"", rules)
        for name in ("loop.md", "skills/loop/SKILL.md", "starter/templates/AGENTS.md"):
            with self.subTest(name=name):
                self.assertIn("legal-checklist.md", (ROOT / name).read_text())
        self.assertIn("publishing legal text", (ROOT / "loop.md").read_text())
        self.assertIn("LEGAL-CHECKLIST.md", (ROOT / "scripts" / "loop-init.mjs").read_text())
        self.assertTrue((ROOT / "starter" / "templates" / "legal-checklist.md").exists())

    def test_resource_guard_and_pause_rules(self):
        policy = (ROOT / "loop.md").read_text()
        for text in ("Rules by task profile", "Unknown readings still block heavy work", "A known warning blocks both",
                     "Unknown is never safe", "Thermal Warning Level: 0", "CPU_Speed_Limit = 100",
                     "has been recorded", "Pause report", "ETA unknown", "Report sync blockers separately",
                     "A docs fix does not update a stored goal"):
            with self.subTest(text=text):
                self.assertIn(text, policy)
        owner = (ROOT / "OWNER-COMMUNICATION.md").read_text()
        for text in ("Blocked by:", "Latest reading:", "Still allowed:", "Restarts when:", "ETA:"):
            with self.subTest(text=text):
                self.assertIn(text, owner)
        self.assertIn("Pause / blockers", (ROOT / "starter" / "templates" / "HANDOFF.md").read_text())
        self.assertIn("Stale stored goal", (ROOT / "tests" / "loop-skill-scenarios.md").read_text())

    def test_safety_and_truth_boundaries_remain_explicit(self):
        policy = (ROOT / "EFFICIENT-WORKFLOW.md").read_text()
        for requirement in (
            "PLANNED", "not executed", "parent model remains unchanged",
            "explicit user-selected model", "human-switch checkpoint",
            "Browser use remains opt-in", "No secrets", "append-only archive",
            "New/untriaged failures block", "not increased", "do not create one without",
            "not push, deploy, fetch", "preserve", "Installation boundary",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, policy)

    def test_followups_not_misrepresented_as_delivery(self):
        policy = (ROOT / "EFFICIENT-WORKFLOW.md").read_text()
        self.assertIn("bounded follow-up tasks", policy)
        self.assertIn("before claiming a cost improvement", policy)


if __name__ == "__main__":
    unittest.main()
