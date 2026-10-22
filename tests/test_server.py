"""Behavior and real stdio checks; no model, production site, or user config access."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ServerTests(unittest.TestCase):
    def setUp(self):
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="ss-test-", dir=local)
        self.base = Path(self.temp.name).resolve()
        assert self.base.is_relative_to(local.resolve())
        self.project = self.base / "project"
        self.project.mkdir()
        self.env = patch.dict(os.environ, {"SS_WORKSPACE_ROOTS": json.dumps([str(self.project)])})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def state(self, rel=".as-state", content=None):
        d = self.project / rel
        d.mkdir(parents=True, exist_ok=True)
        (d / "state.json").write_text(json.dumps(content or {
            "main_problem": "测试 Unicode 路径与状态", "next_smallest_action": "inspect event handler",
            "private_learner_answers": "NOT_RETURNED",
        }, ensure_ascii=False), encoding="utf-8")
        (d / "handoff.md").write_text("# 手动停止与重开\n未上线", encoding="utf-8")
        return d

    def test_status_has_actual_capability_boundary(self):
        result = server.ss_status()
        self.assertFalse(result["writes_state"])
        self.assertFalse(result["calls_models"])
        self.assertEqual(result["skill_sha256"], hashlib.sha256((server.SKILL / "SKILL.md").read_bytes()).hexdigest())

    def test_all_guides_read_and_unknown_rejected(self):
        for topic in server.GUIDES:
            self.assertGreater(len(server.ss_read_guide(topic)["text"]), 50)
        with self.assertRaises(ValueError):
            server.ss_read_guide("../../.env")

    def test_no_state_is_not_initialized(self):
        result = server.ss_project_brief(str(self.project))
        self.assertEqual(result["status"], "no-state")
        self.assertEqual(list(self.project.iterdir()), [])

    def test_dot_state_read_without_modification(self):
        d = self.state()
        before = {p.name: p.read_bytes() for p in d.iterdir()}
        result = server.ss_project_brief(str(self.project))
        self.assertEqual(result["status"], "read")
        self.assertIn("测试", result["files"]["state.json"]["fields"]["main_problem"]["preview"])
        self.assertNotIn("NOT_RETURNED", json.dumps(result))
        self.assertEqual(before, {p.name: p.read_bytes() for p in d.iterdir()})

    def test_tools_layout_supported(self):
        self.state("tools/search-stack/local/as-state")
        self.assertEqual(server.ss_project_brief(str(self.project))["state_layout"], "tools-as-state")

    def test_ambiguous_layout_is_not_merged(self):
        self.state()
        self.state("tools/search-stack/local/as-state")
        result = server.ss_project_brief(str(self.project))
        self.assertEqual(result["status"], "ambiguous")
        self.assertNotIn("files", result)
        self.assertEqual(server.ss_project_brief(str(self.project), "dot-as-state")["status"], "read")

    def test_absolute_scope_required(self):
        for p in (str(self.base), "."):
            with self.assertRaises(ValueError):
                server.ss_project_brief(p)

    def test_no_config_fails_closed(self):
        with patch.dict(os.environ, {"SS_WORKSPACE_ROOTS": "[]"}):
            with self.assertRaises(ValueError):
                server.ss_project_brief(str(self.project))

    def test_invalid_root_config_rejected(self):
        for value in ('{"path":"x"}', '[3]', '["relative"]'):
            with patch.dict(os.environ, {"SS_WORKSPACE_ROOTS": value}):
                with self.assertRaises(ValueError):
                    server.ss_project_brief(str(self.project))

    def test_invalid_json_keeps_usable_handoff(self):
        d = self.state()
        (d / "state.json").write_text("{broken", encoding="utf-8")
        result = server.ss_project_brief(str(self.project))
        self.assertEqual(result["status"], "partial")
        self.assertIn("handoff.md", result["files"])
        self.assertEqual(result["warnings"][0]["file"], "state.json")

    def test_large_file_is_reported_not_silently_ignored(self):
        d = self.state()
        (d / "state.json").write_text("x" * 262145, encoding="utf-8")
        result = server.ss_project_brief(str(self.project))
        self.assertEqual(result["status"], "partial")
        self.assertIn("bounded", result["warnings"][0]["error"])

    def test_long_handoff_is_explicitly_truncated(self):
        d = self.state()
        (d / "handoff.md").write_text("雾" * 7000, encoding="utf-8")
        result = server.ss_project_brief(str(self.project))["files"]["handoff.md"]
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["text"]), 6000)

    def test_link_cannot_escape_project(self):
        external = self.base / "external"
        external.mkdir()
        link = self.project / ".as-state"
        try:
            link.symlink_to(external, target_is_directory=True)
        except OSError as e:
            self.skipTest(f"Directory symlinks unavailable: {type(e).__name__}")
        try:
            with self.assertRaises(ValueError):
                server.ss_project_brief(str(self.project))
        finally:
            link.unlink()

    def test_real_stdio_protocol(self):
        self.state()

        async def exercise():
            params = StdioServerParameters(
                command=sys.executable, args=["-B", str(ROOT / "server.py")],
                env={"SS_WORKSPACE_ROOTS": json.dumps([str(self.project)]), "PYTHONIOENCODING": "utf-8"},
            )
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    init = await session.initialize()
                    self.assertEqual(init.serverInfo.name, "software-stack")
                    tools = (await session.list_tools()).tools
                    self.assertEqual({t.name for t in tools}, {"ss_status", "ss_read_guide", "ss_project_brief"})
                    self.assertTrue(all(t.annotations.readOnlyHint for t in tools))
                    for name, args in [("ss_status", {}), ("ss_read_guide", {"topic": "entry"}),
                                       ("ss_project_brief", {"repo_path": str(self.project)})]:
                        result = await session.call_tool(name, args)
                        self.assertFalse(result.isError)
                        self.assertTrue(result.content)
                    invalid = await session.call_tool("ss_read_guide", {"topic": "bogus"})
                    self.assertTrue(invalid.isError)
                    rejected = await session.call_tool("ss_project_brief", {"repo_path": str(self.base)})
                    self.assertTrue(rejected.isError)
                    resources = await session.list_resources()
                    self.assertEqual([str(r.uri) for r in resources.resources], ["ss://guide/entry"])
                    content = await session.read_resource("ss://guide/entry")
                    self.assertIn("/SS", content.contents[0].text)

        asyncio.run(asyncio.wait_for(exercise(), timeout=30))


if __name__ == "__main__":
    unittest.main(verbosity=2)
