"""Check the EXE self-installer wrote the expected agent registrations."""
import json
from pathlib import Path
import sys
import tomllib

home, exe = Path(sys.argv[1]), str(Path(sys.argv[2]).resolve())
skill = home / ".agents/skills/blender-scene-automation/SKILL.md"
assert skill.is_file(), f"Missing canonical skill: {skill}"
assert "name: blender-scene-automation" in skill.read_text(encoding="utf-8")

for path in (
    ".claude/skills/blender-scene-automation/SKILL.md",
    ".gemini/config/skills/blender-scene-automation/SKILL.md",
    ".gemini/antigravity-cli/skills/blender-scene-automation/SKILL.md",
    ".config/opencode/skills/blender-scene-automation/SKILL.md",
):
    assert (home / path).read_bytes() == skill.read_bytes(), path

for path in (
    ".claude/CLAUDE.md", ".codex/AGENTS.md",
    ".gemini/GEMINI.md", ".config/opencode/AGENTS.md",
):
    assert "<!-- mcp-for-blender managed start -->" in (home / path).read_text(), path

codex = tomllib.loads((home / ".codex/config.toml").read_text())
claude = json.loads((home / ".claude.json").read_text())
antigravity = json.loads((home / ".gemini/config/mcp_config.json").read_text())
opencode = json.loads((home / ".config/opencode/opencode.json").read_text())
desktop = json.loads((home / "AppData/Roaming/Claude/claude_desktop_config.json").read_text())
assert codex["mcp_servers"]["blender"]["command"] == exe
assert claude["mcpServers"]["blender"]["command"] == exe
assert antigravity["mcpServers"]["blender"]["command"] == exe
assert opencode["mcp"]["blender"]["command"] == [exe]
assert desktop["mcpServers"]["blender"]["command"] == exe
print("PASS: 5 agent-family MCP registrations and shared/client skills/instructions")
