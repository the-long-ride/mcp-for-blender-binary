"""Opt-in, stdlib-only installer embedded in the standalone MCP for Blender EXE.

This module runs only under the explicit "install" command. Normal invocation
uses MCP stdio and never accesses or mutates AI-client configuration files.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import tomllib


CLIENTS = (
    "claude", "claude-code", "claude-desktop",
    "codex", "chatgpt", "antigravity", "opencode"
)
ALL_CLIENTS = ("claude", "claude-desktop", "codex", "antigravity", "opencode")
SKILL_NAME = "blender-scene-automation"
SERVER_NAME = "blender"
SKILL_RESOURCE = Path("skills") / SKILL_NAME / "SKILL.md"


def embedded_skill() -> str:
    return (Path(__file__).resolve().parent / SKILL_RESOURCE).read_text(encoding="utf-8")


def executable_path() -> Path:
    if not getattr(sys, "frozen", False):
        raise RuntimeError("The self-installer must run from the packaged mcp-for-blender.exe.")
    exe = Path(sys.executable).resolve()
    if exe.suffix.lower() != ".exe":
        raise RuntimeError(f"Not a Windows executable: {exe}")
    return exe


def _save(path: Path, content: str, dry_run: bool) -> None:
    """Write atomically with backup; do not overwrite original if parsing failed."""
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.is_file()
    if existed:
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    pending = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False,
        ) as stream:
            pending = Path(stream.name)
            stream.write(content)
        os.replace(pending, path)
    finally:
        if pending is not None and pending.exists():
            pending.unlink()


def _skill_paths(client: str, home: Path) -> list[Path]:
    if client == "claude":
        roots = [home / ".agents/skills", home / ".claude/skills"]
    elif client == "codex":
        roots = [home / ".agents/skills"]
    elif client == "antigravity":
        # Antigravity IDE/2.0 and Antigravity CLI have different global roots.
        roots = [home / ".agents/skills", home / ".gemini/config/skills", home / ".gemini/antigravity-cli/skills"]
    elif client == "opencode":
        roots = [home / ".agents/skills", home / ".config/opencode/skills"]
    else:
        roots = []
    return [root / SKILL_NAME / "SKILL.md" for root in roots]


def install_skills(client: str, home: Path, content: str, dry_run: bool) -> None:
    for path in _skill_paths(client, home):
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            print(f"  Skill up to date: {path}")
            continue
        print(f"  Skill -> {path}")
        if not dry_run:
            _save(path, content, dry_run)


def _write_json_server(
    path: Path, section_name: str, entry: dict, dry_run: bool, replace: bool
) -> None:
    if path.is_file():
        try:
            config = json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError(f"Invalid JSON; left untouched: {path}: {exc}") from exc
        if not isinstance(config, dict):
            raise RuntimeError(f"Configuration must be an object: {path}")
    else:
        config = {}
    section = config.setdefault(section_name, {})
    if not isinstance(section, dict):
        raise RuntimeError(f"Configuration section must be an object: {path}: {section_name}")
    existing = section.get(SERVER_NAME)
    if existing == entry:
        print(f"  MCP up to date: {path}")
        return
    if existing is not None and not replace:
        print(f"  Existing MCP entry preserved: {path} (use --replace to update)")
        return
    section[SERVER_NAME] = entry
    print(f"  MCP config -> {path}")
    _save(path, json.dumps(config, ensure_ascii=False, indent=2) + "\n", dry_run)


def _install_codex(exe: Path, home: Path, dry_run: bool, replace: bool) -> None:
    # Shared by Codex CLI, IDE extension, and ChatGPT desktop Codex host.
    codex_home = Path(os.environ["CODEX_HOME"]).expanduser() if os.getenv("CODEX_HOME") else home / ".codex"
    path = codex_home / "config.toml"
    original = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    try:
        parsed = tomllib.loads(original)
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(f"Invalid TOML; left untouched: {path}: {exc}") from exc
    servers = parsed.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise RuntimeError(f"mcp_servers is not a table: {path}")
    current = servers.get(SERVER_NAME)
    if current is not None:
        if not isinstance(current, dict):
            raise RuntimeError(f"Existing MCP server is not a table: {path}")
        if current.get("command") == str(exe) and current.get("startup_timeout_sec", 0) >= 60:
            print(f"  MCP up to date: {path}")
            return
        if not replace:
            print(f"  Existing MCP entry preserved: {path} (use --replace to update)")
            return

    # JSON strings are valid TOML basic quoted strings for local Windows paths.
    section = (
        f"[mcp_servers.{SERVER_NAME}]\n"
        f"command = {json.dumps(str(exe))}\n"
        f"args = []\n"
        f"startup_timeout_sec = 60\n"
    )
    new_text = original
    if current is not None:
        # If an existing section contains nested tables or inline definitions,
        # never rewrite it automatically; that could remove user credentials.
        match = re.search(
            r'(?m)^[ \t]*\[mcp_servers\.(?:"blender"|'
            r"'blender'|blender)\][ \t]*(?:#.*)?$",
            original,
        )
        if not match:
            raise RuntimeError(
                f"Existing Codex entry has a nonstandard TOML layout in {path}; "
                "edit it through ChatGPT desktop Settings > MCP servers."
            )
        next_table = re.search(r"(?m)^[ \t]*\[{1,2}[^]\r\n]+]{1,2}[ \t]*(?:#.*)?$", original[match.end():])
        end = match.end() + next_table.start() if next_table else len(original)
        # A nested table can inherit parent settings; do not silently leave one
        # attached to our replaced entry with possibly incompatible options.
        if next_table:
            nxt = next_table.group(0).lstrip()
            if nxt.startswith("[mcp_servers.blender.") or nxt.startswith('["mcp_servers.blender.'):
                raise RuntimeError(f"Nested MCP tables detected; edit manually: {path}")
        new_text = original[:match.start()] + section + "\n" + original[end:]
    else:
        new_text = original.rstrip() + ("\n\n" if original.strip() else "") + section

    try:
        validated = tomllib.loads(new_text)
        assert validated["mcp_servers"][SERVER_NAME]["command"] == str(exe)
    except (tomllib.TOMLDecodeError, KeyError, AssertionError) as exc:
        raise RuntimeError(f"Refusing to write invalid Codex TOML: {path}: {exc}") from exc
    print(f"  Codex / ChatGPT desktop MCP config -> {path}")
    _save(path, new_text, dry_run)


def _claude_desktop_path(home: Path) -> Path:
    """Support normal Windows and existing MSIX-virtualized Claude profiles."""
    local_root = home / "AppData/Local/Packages"
    if local_root.is_dir():
        for package in sorted(local_root.glob("Claude_*")):
            virtual = package / "LocalCache/Roaming/Claude/claude_desktop_config.json"
            if virtual.is_file():
                return virtual
    appdata = os.getenv("APPDATA") if home == Path.home() else None
    root = Path(appdata) if appdata else home / "AppData/Roaming"
    return root / "Claude/claude_desktop_config.json"


def _install_opencode(exe: Path, home: Path, dry_run: bool, replace: bool) -> None:
    root = home / ".config/opencode"
    config_env = os.getenv("OPENCODE_CONFIG")
    path = Path(config_env).expanduser() if config_env else root / "opencode.json"
    # JSONC with comments is supported by OpenCode but not by json.loads.
    if path.suffix.lower() == ".jsonc" or (
        not path.exists() and path.with_suffix(".jsonc").is_file()
    ):
        raise RuntimeError(
            "Existing OpenCode JSONC configuration needs in-app/manual editing "
            f"to preserve comments: {path.with_suffix('.jsonc')}"
        )
    _write_json_server(
        path, "mcp",
        {"type": "local", "command": [str(exe)], "enabled": True, "timeout": 60000},
        dry_run, replace,
    )



# Scoped additions to global AI-client instructions. The only managed section
# is this block; existing instructions before/after it remain untouched.
RULE_START = "<!-- mcp-for-blender managed start -->"
RULE_END = "<!-- mcp-for-blender managed end -->"
RULE_TEXT = """When the task involves Blender 3D modeling or scene editing, use the
\`blender\` MCP server and the \`blender-scene-automation\` skill installed in
~/.agents/skills/blender-scene-automation/SKILL.md. Start by inspecting the addon
and scene; confirm results through viewport inspection. Treat execute_blender_code
as arbitrary Python execution in the user's Blender: ask before destructive,
external-network, or irreversible actions. Do not claim a scene was modified
unless a tool result confirms it.
"""


def install_instructions(client: str, home: Path, dry_run: bool) -> None:
    paths = {
        "claude": home / ".claude/CLAUDE.md",
        "codex": (Path(os.environ["CODEX_HOME"]).expanduser()
                  if os.getenv("CODEX_HOME") and home == Path.home()
                  else home / ".codex") / "AGENTS.md",
        "antigravity": home / ".gemini/GEMINI.md",
        "opencode": home / ".config/opencode/AGENTS.md",
    }
    path = paths.get(client)
    if path is None:
        return
    previous = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    block = RULE_START + "\n" + RULE_TEXT.rstrip() + "\n" + RULE_END
    if (RULE_START in previous) != (RULE_END in previous):
        raise RuntimeError(f"Incomplete managed instruction block, left untouched: {path}")
    if RULE_START in previous:
        left = previous.index(RULE_START)
        right = previous.index(RULE_END, left) + len(RULE_END)
        updated = previous[:left] + block + previous[right:]
    else:
        updated = previous.rstrip() + ("\n\n" if previous.strip() else "") + block + "\n"
    if updated == previous:
        print(f"  Instructions up to date: {path}")
        return
    print(f"  Instructions -> {path}")
    _save(path, updated, dry_run)


def install(
    targets: list[str], exe: Path, home: Path, content: str,
    dry_run: bool = False, replace: bool = False,
) -> int:
    failures = 0
    aliases = {"claude-code": "claude", "chatgpt": "codex"}
    for original in targets:
        client = aliases.get(original, original)
        print(f"[{original}]")
        try:
            if client == "claude":
                _write_json_server(
                    home / ".claude.json", "mcpServers",
                    {"type": "stdio", "command": str(exe), "args": []},
                    dry_run, replace,
                )
            elif client == "claude-desktop":
                _write_json_server(
                    _claude_desktop_path(home), "mcpServers",
                    {"command": str(exe), "args": []},
                    dry_run, replace,
                )
            elif client == "codex":
                _install_codex(exe, home, dry_run, replace)
            elif client == "antigravity":
                _write_json_server(
                    home / ".gemini/config/mcp_config.json", "mcpServers",
                    {"command": str(exe), "args": []},
                    dry_run, replace,
                )
            elif client == "opencode":
                _install_opencode(exe, home, dry_run, replace)
            else:
                raise ValueError(f"Unknown client: {original}")
            install_skills(client, home, content, dry_run)
            install_instructions(client, home, dry_run)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            failures += 1
    if dry_run:
        print("Dry run: no configuration or skill files changed.")
    elif not failures:
        print("Installed. Restart desktop apps/IDEs to reload MCP and skills.")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcp-for-blender.exe install",
        description="Install embedded Blender skills and MCP server for desktop/CLI AI clients.",
    )
    parser.add_argument("client", nargs="?", choices=CLIENTS, help="Client (or chatgpt alias for Codex host)")
    parser.add_argument("--all", action="store_true", help="Configure all supported client families")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing files")
    parser.add_argument("--replace", action="store_true", help="Replace existing blender entries")
    parser.add_argument("--home", type=Path, default=None, help=argparse.SUPPRESS)
    options = parser.parse_args(argv)
    if bool(options.client) == bool(options.all):
        parser.error("specify a client or --all")
    try:
        return install(
            list(ALL_CLIENTS) if options.all else [options.client],
            executable_path(), (options.home.expanduser() if options.home else Path.home()), embedded_skill(),
            options.dry_run, options.replace,
        )
    except (RuntimeError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
