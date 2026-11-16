"""End-to-end help and per-client installation smoke test of the frozen EXE."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


EXE = Path(sys.argv[1]).resolve()


def run(*args: str) -> str:
    result = subprocess.run(
        [str(EXE), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=45,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{EXE.name} {' '.join(args)} returned {result.returncode}\n"
            f"stdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}"
        )
    return result.stdout


help_cases = {
    ("--help",): ("install", "agents", "bundle", "install-addon", "setup", "update"),
    ("install", "--help"): ("codex", "claude", "antigravity", "opencode", "--all", "--dry-run", "--replace"),
    ("agents", "--help"): ("install",),
    ("agents", "install", "--help"): ("--target", "all", "codex", "claude", "antigravity", "opencode"),
    ("bundle", "--help"): ("verify", "license", "docs"),
    ("bundle", "verify", "--help"): ("--json",),
    ("bundle", "license", "--help"): ("license",),
    ("bundle", "docs", "--help"): ("docs",),
    ("install-addon", "--help"): ("--addons-dir",),
    ("addon-paths", "--help"): ("addon-paths",),
    ("setup", "--help"): ("--dry-run", "--skip-addon"),
    ("update", "--help"): ("--dry-run",),
    ("help", "install"): ("--all", "codex"),
}
for agent in ("codex", "claude", "antigravity", "opencode",
              "claude-desktop", "claude-code", "chatgpt"):
    help_cases[("install", agent, "--help")] = (agent, "--dry-run", "--replace")

for command, expected in help_cases.items():
    response = run(*command)
    assert "usage:" in response.lower(), f"No usage in {command}: {response[:500]}"
    for word in expected:
        assert word in response, f"{command} help missing {word!r}"
print(f"PASS: {len(help_cases)} help entrypoints return the expected commands/options")

configurations = {
    "codex": ".codex/config.toml",
    "claude": ".claude.json",
    "antigravity": ".gemini/config/mcp_config.json",
    "opencode": ".config/opencode/opencode.json",
}
for client, expected in configurations.items():
    with tempfile.TemporaryDirectory() as directory:
        home = Path(directory)
        run("install", client, "--dry-run", "--home", directory)
        assert not list(home.iterdir()), f"Dry-run for {client} modified the home directory"
        run("install", client, "--home", directory)
        assert (home / expected).is_file(), f"{client} registration missing"
        assert (home / ".agents/skills/blender-scene-automation/SKILL.md").is_file()
        for other in set(configurations.values()) - {expected}:
            assert not (home / other).exists(), f"{client} unexpectedly modified {other}"

with tempfile.TemporaryDirectory() as directory:
    run("agents", "install", "--target", "codex", "--home", directory)
    assert (Path(directory) / configurations["codex"]).is_file()
    for other in ("claude", "antigravity", "opencode"):
        assert not (Path(directory) / configurations[other]).exists()

print("PASS: independent per-agent registration and agents --target alias")
