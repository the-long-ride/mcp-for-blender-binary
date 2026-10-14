"""Standalone installer regression tests (no AI client binaries required)."""
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from blender_mcp import installer, bundle_cli


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.exe = self.home / "mcp-for-blender.exe"
        self.exe.write_bytes(b"test")
        self.skill = installer.embedded_skill()

    def run_install(self, targets=None, **kwargs):
        with patch.dict(os.environ, {"CODEX_HOME": ""}):
            return installer.install(targets or list(installer.ALL_CLIENTS),
                                     self.exe, self.home, self.skill, **kwargs)

    def test_bundle_manifest_from_source(self):
        contents = bundle_cli.report()
        self.assertEqual(contents["status"], "ok")
        self.assertFalse(contents["onefile_runtime"])
        for item in ("addon", "skill", "viewport", "license", "documentation"):
            self.assertGreater(contents["assets"][item], 100)

    def test_embedded_skill_resource(self):
        self.assertIn("name: blender-scene-automation", self.skill)
        self.assertIn("execute_blender_code", self.skill)

    def test_all_clients_and_canonical_skill(self):
        self.assertEqual(self.run_install(), 0)
        canonical = self.home / ".agents/skills/blender-scene-automation/SKILL.md"
        self.assertEqual(canonical.read_text(encoding="utf-8"), self.skill)
        for client in ("claude", "codex", "antigravity", "opencode"):
            for path in installer._skill_paths(client, self.home):
                self.assertEqual(path.read_text(encoding="utf-8"), self.skill)
        self.assertEqual(json.loads((self.home / ".claude.json").read_text())
                         ["mcpServers"]["blender"]["command"], str(self.exe))
        self.assertEqual(json.loads((self.home / ".gemini/config/mcp_config.json").read_text())
                         ["mcpServers"]["blender"]["command"], str(self.exe))
        self.assertEqual(json.loads((self.home / ".config/opencode/opencode.json").read_text())
                         ["mcp"]["blender"]["command"], [str(self.exe)])
        self.assertEqual(tomllib.loads((self.home / ".codex/config.toml").read_text())
                         ["mcp_servers"]["blender"]["command"], str(self.exe))
        for target in (".claude/CLAUDE.md", ".codex/AGENTS.md",
                       ".gemini/GEMINI.md", ".config/opencode/AGENTS.md"):
            self.assertIn(installer.RULE_START,
                          (self.home / target).read_text(encoding="utf-8"))

    def test_idempotent_install(self):
        self.assertEqual(self.run_install(), 0)
        watched = [self.home / ".codex/config.toml", self.home / ".claude/CLAUDE.md"]
        original = [path.read_bytes() for path in watched]
        self.assertEqual(self.run_install(), 0)
        self.assertEqual(original, [path.read_bytes() for path in watched])

    def test_dry_run_does_not_create_anything(self):
        self.assertEqual(self.run_install(dry_run=True), 0)
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".codex").exists())
        self.assertFalse((self.home / ".claude.json").exists())

    def test_merges_existing_rules_and_unrelated_mcp(self):
        instructions = self.home / ".gemini/GEMINI.md"
        instructions.parent.mkdir(parents=True)
        instructions.write_text("# Existing private rule\n", encoding="utf-8")
        cfg = self.home / ".gemini/config/mcp_config.json"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "other.exe"}},
                                   "theme": "dark"}), encoding="utf-8")
        self.assertEqual(self.run_install(["antigravity"]), 0)
        self.assertTrue(instructions.read_text().startswith("# Existing private rule"))
        self.assertIn(installer.RULE_END, instructions.read_text())
        parsed = json.loads(cfg.read_text())
        self.assertEqual(parsed["mcpServers"]["other"]["command"], "other.exe")
        self.assertEqual(parsed["theme"], "dark")
        self.assertTrue(cfg.with_suffix(".json.bak").exists())

    def test_existing_blender_preserved_unless_replace(self):
        cfg = self.home / ".claude.json"
        cfg.write_text(json.dumps({"mcpServers": {"blender": {"command": "uvx"}}}))
        self.assertEqual(self.run_install(["claude"]), 0)
        self.assertEqual(json.loads(cfg.read_text())["mcpServers"]["blender"]["command"], "uvx")
        self.assertEqual(self.run_install(["claude"], replace=True), 0)
        self.assertEqual(json.loads(cfg.read_text())["mcpServers"]["blender"]["command"], str(self.exe))

    def test_invalid_config_not_overwritten(self):
        cfg = self.home / ".claude.json"
        cfg.write_text("{ not valid json", encoding="utf-8")
        self.assertEqual(self.run_install(["claude"]), 1)
        self.assertEqual(cfg.read_text(), "{ not valid json")

    def test_codex_preserves_other_tables(self):
        cfg = self.home / ".codex/config.toml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text('model = "gpt-6"\n\n[mcp_servers.other]\ncommand = "old.exe"\n')
        self.assertEqual(self.run_install(["codex"]), 0)
        parsed = tomllib.loads(cfg.read_text())
        self.assertEqual(parsed["model"], "gpt-6")
        self.assertEqual(parsed["mcp_servers"]["other"]["command"], "old.exe")
        self.assertEqual(parsed["mcp_servers"]["blender"]["command"], str(self.exe))

    def test_existing_opencode_jsonc_preserved(self):
        cfg = self.home / ".config/opencode/opencode.jsonc"
        cfg.parent.mkdir(parents=True)
        cfg.write_text("// personal comments\n{}\n")
        self.assertEqual(self.run_install(["opencode"]), 1)
        self.assertEqual(cfg.read_text(), "// personal comments\n{}\n")

    def test_instruction_marker_mismatch_is_protected(self):
        path = self.home / ".claude/CLAUDE.md"
        path.parent.mkdir(parents=True)
        path.write_text(installer.RULE_START + "\nmy content\n")
        self.assertEqual(self.run_install(["claude"]), 1)
        self.assertEqual(path.read_text(), installer.RULE_START + "\nmy content\n")


if __name__ == "__main__":
    unittest.main()
