import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("registration", ROOT / "scripts/register_local.py")
reg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg)


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=local, prefix="registration-")
        self.home = Path(self.tmp.name).resolve()
        assert self.home.is_relative_to(local.resolve())
        (self.home / ".codex").mkdir()
        self.codex = self.home / ".codex/config.toml"
        self.claude = self.home / ".claude.json"
        self.codex.write_text('model = "keep-model"\n[mcp_servers.as]\ncommand = "keep-as"\n', encoding="utf-8")
        self.claude.write_text(json.dumps({"preferences": {"keep": True}, "mcpServers": {
            "search-stack-orchestrator": {"command": "keep-as", "env": {"EXAMPLE": "fake-test-value"}}}}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_makes_no_changes(self):
        before = reg.files_under(self.home)
        result = reg.install(self.home, [ROOT])
        self.assertFalse(result["applied"])
        self.assertEqual(before, reg.files_under(self.home))

    def test_additive_install_and_idempotency(self):
        before_c = json.loads(self.claude.read_text())
        before_x = tomllib.loads(self.codex.read_text())
        result = reg.install(self.home, [ROOT], True)
        self.assertTrue(result["installed_skill_matches"])
        self.assertTrue((self.home / ".claude/commands/SS.md").is_file())
        c = json.loads(self.claude.read_text(encoding="utf-8"))
        x = tomllib.loads(self.codex.read_text(encoding="utf-8"))
        del c["mcpServers"]["software-stack"]
        del x["mcp_servers"]["software-stack"]
        self.assertEqual(c, before_c)
        self.assertEqual(x, before_x)
        after = reg.files_under(self.home)
        second = reg.install(self.home, [ROOT], True)
        self.assertEqual(second["changes"], 0)
        self.assertEqual(after, reg.files_under(self.home))

    def test_conflict_does_not_overwrite_anything(self):
        data = json.loads(self.claude.read_text())
        data["mcpServers"]["software-stack"] = {"command": "user-owned"}
        self.claude.write_text(json.dumps(data), encoding="utf-8")
        before = reg.files_under(self.home)
        with self.assertRaises(ValueError):
            reg.install(self.home, [ROOT], True)
        self.assertEqual(before, reg.files_under(self.home))

    def test_existing_command_conflict_preserved(self):
        d = self.home / ".claude/commands"
        d.mkdir(parents=True)
        (d / "SS.md").write_text("user content", encoding="utf-8")
        before = reg.files_under(self.home)
        with self.assertRaises(ValueError):
            reg.install(self.home, [ROOT], True)
        self.assertEqual(before, reg.files_under(self.home))


if __name__ == "__main__":
    unittest.main(verbosity=2)
