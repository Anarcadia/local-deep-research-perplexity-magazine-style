import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
SCRIPT = SKILL_DIR / "scripts" / "configure.py"
SPEC = importlib.util.spec_from_file_location("configure", SCRIPT)
configure = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(configure)
import research_tools
import select_tools


class PublicSkillTest(unittest.TestCase):
    def test_welcome_recommends_exa_and_gives_setup_locations(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("建议务必配置完 Exa API", skill)
        self.assertIn("每月 20,000 次请求", skill)
        self.assertIn("https://exa.ai/", skill)
        self.assertIn("https://dashboard.exa.ai/api-keys", skill)
        self.assertIn("<skill-dir>/config/.env.local", skill)
        self.assertEqual(configure.EXA_API_KEYS, "https://dashboard.exa.ai/api-keys")

    def test_optional_providers_are_disabled_by_default(self):
        config = json.loads((SKILL_DIR / "config" / "tools.example.json").read_text())
        for tool_id in ["exa", "perplexity", "grok_build", "kimi_code"]:
            self.assertFalse(config["tools"][tool_id]["enabled"])

    def test_all_provider_fields_are_present(self):
        config = json.loads((SKILL_DIR / "config" / "tools.example.json").read_text())
        fields = {
            "enabled", "required", "role", "perspective", "invocation", "command",
            "env_key", "auth_modes", "setup_command", "endpoint", "capabilities",
            "limitations", "fallback",
            "selection_required", "readiness_checks",
        }
        for spec in config["tools"].values():
            self.assertTrue(fields.issubset(spec))

    def test_initializer_creates_private_local_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            (config_dir / "tools.example.json").write_text(
                (SKILL_DIR / "config" / "tools.example.json").read_text()
            )
            (config_dir / ".env.example").write_text(
                (SKILL_DIR / "config" / ".env.example").read_text()
            )
            tools_file, env_file = configure.initialize_files(config_dir)
            self.assertTrue(tools_file.exists())
            self.assertTrue(env_file.exists())
            self.assertEqual(env_file.stat().st_mode & 0o777, 0o600)

    def test_status_never_contains_secret_values(self):
        config = json.loads((SKILL_DIR / "config" / "tools.example.json").read_text())
        config["configured"] = True
        config["tools"]["exa"]["enabled"] = True
        result = configure.status(config, {"EXA_API_KEY": "secret-test-value"})
        rendered = json.dumps(result)
        self.assertNotIn("secret-test-value", rendered)
        self.assertTrue(result["tools"]["exa"]["credential_ready"])

    def test_run_selection_supports_all_individual_and_none(self):
        self.assertEqual(select_tools.parse_selection("all"), configure.OPTIONAL_TOOLS)
        self.assertEqual(select_tools.parse_selection("exa,grok,kimi"), ["exa", "grok_build", "kimi_code"])
        self.assertEqual(select_tools.parse_selection("none"), [])

    def test_unconfigured_selected_provider_is_unavailable(self):
        config = json.loads((SKILL_DIR / "config" / "tools.example.json").read_text())
        result = select_tools.build_selection(["exa"], config, {})
        self.assertEqual(result["active"], [])
        self.assertEqual(result["unavailable"], ["exa"])
        self.assertFalse(result["tools"]["exa"]["active"])

    def test_active_selection_controls_provider_calls(self):
        config = json.loads((SKILL_DIR / "config" / "tools.example.json").read_text())
        config["configured"] = True
        config["tools"]["exa"]["enabled"] = True
        result = select_tools.build_selection(["exa"], config, {"EXA_API_KEY": "test-key"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tool-selection.json"
            path.write_text(json.dumps(result))
            research_tools.load_selection(str(path), "exa")
            with self.assertRaises(ValueError):
                research_tools.load_selection(str(path), "perplexity")

    def test_grok_and_kimi_use_headless_search_commands(self):
        class Args:
            query = "test query"
            cwd = None
            timeout = 30

        config = json.loads((SKILL_DIR / "config" / "tools.example.json").read_text())
        completed = type("Completed", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
        with patch.object(research_tools.subprocess, "run", return_value=completed) as run:
            research_tools.run_cli("grok_build", Args(), {}, config)
            grok_args = run.call_args.args[0]
            self.assertIn("quick-search", grok_args)
            self.assertIn("--single", grok_args)
            research_tools.run_cli("kimi_code", Args(), {}, config)
            kimi_args = run.call_args.args[0]
            self.assertIn("--prompt", kimi_args)
            self.assertIn("text", kimi_args)

    def test_public_files_contain_no_private_markers(self):
        forbidden = [
            "/" + "Users" + "/",
            "yun" + "hanbao",
            "船" + "板",
            "Zen" + "Mux",
            "codex" + "-search",
            "D" + "052",
            "R" + "020",
        ]
        for path in SKILL_DIR.rglob("*"):
            if not path.is_file() or path.suffix in {".pyc"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{marker} found in {path}")


if __name__ == "__main__":
    unittest.main()
