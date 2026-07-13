import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
SCRIPT = SKILL_DIR / "scripts" / "production_model_router.py"
SPEC = importlib.util.spec_from_file_location("production_model_router", SCRIPT)
router = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(router)
import select_writer


class ModelRouterTest(unittest.TestCase):
    def setUp(self):
        self.config = router.load_config()

    def test_openrouter_replaces_anthropic_compatible_backend(self):
        self.assertNotIn("zenmux", self.config["backends"])
        backend = self.config["backends"]["openrouter"]
        self.assertEqual(backend["base_url"], "https://openrouter.ai/api/v1")
        self.assertEqual(backend["type"], "openai_compatible_api")

    def test_expected_model_ids(self):
        models = self.config["backends"]["openrouter"]["models"]
        self.assertNotIn("sonnet-4.5", models)
        self.assertEqual(models["glm-5.2"]["model"], "z-ai/glm-5.2")
        self.assertEqual(models["opus-4.6"]["model"], "anthropic/claude-opus-4.6")
        self.assertEqual(models["sonnet-5"]["model"], "anthropic/claude-sonnet-5")
        self.assertEqual(models["gemini-3.1-pro-preview"]["model"], "google/gemini-3.1-pro-preview")

    def test_no_paid_fallback_or_monetary_budget(self):
        self.assertFalse(self.config["allow_automatic_fallback"])
        backend = self.config["backends"]["openrouter"]
        _, spec = router.resolve_model("openrouter", backend, "sonnet-5")
        payload = router.openrouter_payload(spec, "write")
        self.assertNotIn("max_tokens", payload)
        self.assertNotIn("max_budget_usd", json.dumps(payload))

    def test_context_bundle_excludes_existing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outline.md").write_text("unordered evidence map")
            (root / "report.md").write_text("old report must not leak")
            bundled = router.bundle_context(self.config, root, "write")
            self.assertIn("unordered evidence map", bundled)
            self.assertNotIn("old report must not leak", bundled)

    def test_status_does_not_expose_key(self):
        backend = self.config["backends"]["openrouter"]
        _, spec = router.resolve_model("openrouter", backend, "glm-5.2")
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "secret-test-key"}, clear=False):
            status = router.route_status("openrouter", spec)
        self.assertTrue(status["ready"])
        self.assertNotIn("secret-test-key", json.dumps(status))

    def test_default_writer_is_current_agent(self):
        self.assertEqual(self.config["default_backend"], "agent")
        name, backend = router.resolve_backend(self.config, None)
        self.assertEqual(name, "agent")
        self.assertEqual(backend["type"], "host_native")

    def test_glm_supports_writing_and_independent_audit(self):
        backend = self.config["backends"]["openrouter"]
        _, glm = router.resolve_model("openrouter", backend, "glm-5.2")
        router.require_role(glm, "writing")
        router.require_role(glm, "audit")
        self.assertEqual(glm["reasoning_effort"], "high")
        self.assertEqual(
            router.openrouter_payload(glm, "write")["reasoning"],
            {"effort": "high"},
        )
        _, opus = router.resolve_model("openrouter", backend, "opus-4.6")
        self.assertEqual(opus["reasoning_effort"], "medium")
        with self.assertRaises(ValueError):
            router.require_role(opus, "audit")

    def test_audit_context_includes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "report.md").write_text("draft report")
            (root / "evidence-ledger.md").write_text("claims")
            bundled = router.bundle_context(self.config, root, "audit", task="audit")
            self.assertIn("draft report", bundled)
            self.assertIn("claims", bundled)

    def test_writer_selection_notice_and_agent_route(self):
        self.assertEqual(
            select_writer.NOTICE,
            "如果用户处于OpenAI Anthropic Google可服务国家范围之外，则Openrouter源中目前配置唯一可用的"
            "替代写作模型是GLM-5.2，用户只能选择此模型，或者解除Openrouter账户的限制，又或者自己让AI"
            "改写skill，修改后端模型id为其他可用模型。",
        )
        selection = select_writer.build_selection("agent", self.config)
        self.assertTrue(selection["ready"])
        self.assertEqual(selection["backend"], "agent")
        self.assertIn("report_writing", selection["roles"])

    def test_default_style_and_unordered_contract_remain_fixed(self):
        effective = router.apply_default_style(self.config, "write", "default")
        self.assertIn("地道中文", effective)
        self.assertIn("大众人文杂志", effective)
        self.assertIn("避免列表清单", effective)
        self.assertIn("无序", effective)
        self.assertIn("不要沿用其行顺序", effective)


if __name__ == "__main__":
    unittest.main()
