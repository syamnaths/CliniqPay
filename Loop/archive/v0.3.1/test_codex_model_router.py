import importlib.util
import io
from pathlib import Path
from contextlib import redirect_stdout
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "codex_model_router.py"
SPEC = importlib.util.spec_from_file_location("codex_model_router", SCRIPT)
router = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(router)


class CodexModelRouterTests(unittest.TestCase):
    def setUp(self):
        self.policy = router.load_policy(ROOT / "config" / "model-routing.json")

    def test_task_classes_select_expected_current_models(self):
        self.assertEqual(router.candidates_for(self.policy, "simple")[0], {
            "model": "gpt-5.6-luna",
            "effort": "low",
        })
        self.assertEqual(router.candidates_for(self.policy, "standard")[0]["model"], "gpt-5.6-terra")
        self.assertEqual(router.candidates_for(self.policy, "reasoning")[0]["model"], "gpt-5.6-sol")
        self.assertEqual(router.candidates_for(self.policy, "high-risk")[0], {
            "model": "gpt-6-astra",
            "effort": "high",
        })
        self.assertEqual(router.candidates_for(self.policy, "large-context")[0], {
            "model": "gpt-6-astra",
            "effort": "medium",
        })

    def test_auto_classifier_routes_by_task_intensity(self):
        self.assertEqual(router.classify_task("status of current git diff"), "simple")
        self.assertEqual(router.classify_task("make the label opacity smaller"), "focused")
        self.assertEqual(router.classify_task("implement the approved audio fix"), "standard")
        self.assertEqual(router.classify_task("diagnose the root cause of this complex audio bug"), "reasoning")
        self.assertEqual(router.classify_task("map the whole app and every flow"), "large-context")
        self.assertEqual(router.classify_task("verify the responsive visual layout in browser"), "browser")
        self.assertEqual(router.classify_task("merge, deploy, and push this production release"), "high-risk")

    def test_auto_plan_uses_prompt_classification(self):
        class Args:
            task_class = router.AUTO_TASK_CLASS
            mode = "new"
            session_id = None
            project_root = ROOT
            prompt_file = None
            route_id = "route-test-auto"
            codex_bin = "codex"
            execute = False
            no_record = True

        original_stdin = router.sys.stdin
        try:
            router.sys.stdin = type("FakeStdin", (), {
                "isatty": lambda self: False,
                "read": lambda self: "audit the entire app architecture map",
            })()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(router.execute_route(Args(), self.policy), 0)
        finally:
            router.sys.stdin = original_stdin

    def test_fork_command_uses_model_override_without_prompt(self):
        candidate = router.candidates_for(self.policy, "reasoning")[0]
        command = router.build_command(
            "codex", "fork", candidate, Path("/tmp/project"), "session-123"
        )
        self.assertEqual(command[:3], ["codex", "exec", "fork"])
        self.assertIn("gpt-5.6-sol", command)
        self.assertIn('model_reasoning_effort="high"', command)
        self.assertEqual(command[-2:], ["session-123", "-"])

    def test_routed_prompt_prevents_recursive_routing(self):
        prompt = router.routed_prompt("Implement the bounded change", "route-1", "standard")
        self.assertIn(router.CHILD_MARKER, prompt)
        self.assertIn("Do not invoke or delegate to another model-routing adapter", prompt)
        self.assertIn("Implement the bounded change", prompt)

    def test_decision_log_does_not_need_prompt_content(self):
        digest = router.prompt_digest("private bounded task")
        self.assertEqual(len(digest), 64)
        self.assertNotIn("private bounded task", digest)

    def test_unknown_class_is_rejected(self):
        with self.assertRaises(router.RoutingError):
            router.candidates_for(self.policy, "unknown")

    def test_empty_prompt_cannot_be_auto_classified(self):
        with self.assertRaises(router.RoutingError):
            router.classify_task("  ")

    def test_structured_usage_error_is_account_wide(self):
        output = (
            '{"type":"error","message":"You have hit your usage limit."}\n'
            '{"type":"turn.failed","error":{"message":"Purchase more credits."}}\n'
        )
        message = router.structured_error(output)
        self.assertEqual(message, "Purchase more credits.")
        self.assertEqual(router.failure_kind(message), "account-usage-limit")
        self.assertTrue(router.is_global_failure(message))


if __name__ == "__main__":
    unittest.main()
