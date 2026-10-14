"""Discoverable command help for the standalone EXE.

This module is deliberately stdlib-only. No Blender/MCP imports occur on
--help or under the 'agents install' command so these commands remain fast,
offline and side-effect free.
"""
from __future__ import annotations

import argparse

PROGRAM = "mcp-for-blender.exe"
CLIENT_HELP = {
    "codex": "Codex CLI, IDE extension and ChatGPT Codex host",
    "claude": "Claude Code (user-level MCP server and skill)",
    "antigravity": "Antigravity IDE and CLI integration",
    "opencode": "OpenCode user-level MCP server and skill",
    "claude-desktop": "Claude Desktop (MCP only, no coding-agent rules)",
    "claude-code": "Alias for Claude Code",
    "chatgpt": "Alias for Codex",
}

INSTALL_EXAMPLES = """Examples:
  mcp-for-blender.exe install codex
  mcp-for-blender.exe install claude
  mcp-for-blender.exe install antigravity
  mcp-for-blender.exe install opencode
  mcp-for-blender.exe install claude-desktop
  mcp-for-blender.exe install --all
  mcp-for-blender.exe install codex --dry-run
  mcp-for-blender.exe install codex --replace

Every install registers the local EXE as an MCP server and installs the
Blender skill and agent instructions (where supported).
The canonical skill goes under ~/.agents/skills/blender-scene-automation/.
Existing 'blender' MCP entries are preserved unless --replace is supplied.
"""

def _parser(prog: str, description: str, epilog: str = "") -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=prog,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def _common_install_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing any user files")
    parser.add_argument("--replace", action="store_true", help="Replace an existing 'blender' MCP registration")
    parser.add_argument("--home", help=argparse.SUPPRESS)


def build_parser() -> argparse.ArgumentParser:
    parser = _parser(
        PROGRAM,
        "Standalone Blender MCP server, bundled addon, and AI agent setup.",
        """Running without arguments starts MCP over stdio (for AI agents).

Examples:
  mcp-for-blender.exe --help
  mcp-for-blender.exe install --help
  mcp-for-blender.exe install codex --help
  mcp-for-blender.exe agents install --help
  mcp-for-blender.exe bundle verify
  mcp-for-blender.exe install-addon
  mcp-for-blender.exe --host localhost --port 9876
""",
    )
    parser.add_argument("--host", help="Blender socket host when running MCP (default: BLENDER_HOST or localhost)")
    parser.add_argument("--port", type=int, help="Blender socket port when running MCP (default: BLENDER_PORT)")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    installer = commands.add_parser(
        "install", help="Register MCP + skills + instructions for one agent or all agents",
        description="Choose one AI client, or --all to configure every supported client.",
        epilog=INSTALL_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    installer.add_argument("--all", action="store_true", help="Install for all AI clients (Codex, Claude Code/Desktop, Antigravity, OpenCode)")
    _common_install_options(installer)
    choices = installer.add_subparsers(dest="client", metavar="CLIENT")
    for client, detail in CLIENT_HELP.items():
        p = choices.add_parser(
            client, help=detail,
            description=f"Install the embedded Blender MCP integration for {detail}.",
            epilog=f"Example: {PROGRAM} install {client} --dry-run\n\n"
                   "Only this selected client will be configured. "
                   "Use --replace to update an existing blender server.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        _common_install_options(p)

    agents = commands.add_parser(
        "agents", help="AI agent management commands",
        description="Manage supported AI client integrations.",
    )
    agent_commands = agents.add_subparsers(dest="agent_command", metavar="COMMAND")
    agent_install = agent_commands.add_parser(
        "install", help="Install for a chosen agent, using --target",
        description="Register the embedded MCP server, skills and instructions for a specific AI agent.",
        epilog=INSTALL_EXAMPLES + "\nAlternative: mcp-for-blender.exe agents install --target codex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_install.add_argument("--target", required=True,
                               choices=(*CLIENT_HELP.keys(), "all"),
                               help="Agent to configure, or 'all'")
    _common_install_options(agent_install)

    bundle = commands.add_parser(
        "bundle", help="Inspect resources embedded inside this one-file executable",
        description="Inspect the embedded assets, license and usage documentation.",
    )
    bundle_commands = bundle.add_subparsers(dest="bundle_command", metavar="COMMAND")
    verify = bundle_commands.add_parser(
        "verify", help="Validate bundled addon, skills, guides and resources",
        description="Check the EXE contains the addon, skill, guides, viewport, license and docs.",
    )
    verify.add_argument("--json", action="store_true", help="Print machine-readable resource results")
    bundle_commands.add_parser("license", help="Print the license embedded in the EXE")
    bundle_commands.add_parser("docs", help="Print the Windows binary installation guide")

    addon = commands.add_parser(
        "install-addon", help="Install the bundled addon into Blender",
        description="Extract and install the embedded addon.py to Blender's user addon folder.",
    )
    addon.add_argument("--addons-dir", help="Override Blender's user addons folder")
    commands.add_parser("addon-paths", help="Show Blender user addon locations")
    setup = commands.add_parser("setup", help="Legacy interactive setup for uv-based installs")
    setup.add_argument("--dry-run", action="store_true", help="Preview changes")
    setup.add_argument("-y", "--yes", action="store_true", help="Accept detected clients")
    setup.add_argument("--skip-addon", action="store_true", help="Do not install the addon")
    update = commands.add_parser("update", help="Legacy package/addon update command")
    update.add_argument("--dry-run", action="store_true", help="Preview changes")

    return parser


def print_help_for(argv: list[str]) -> int:
    """Parse a help-only invocation without invoking the MCP server or writing config."""
    parser = build_parser()
    parser.parse_args(argv)
    return 0


def agent_install_arguments(argv: list[str]) -> list[str]:
    """Convert 'agents install --target X' to the embedded installer CLI args."""
    parser = build_parser()
    parsed = parser.parse_args(["agents", *argv])
    if parsed.agent_command != "install":
        parser.parse_args(["agents", "--help"])
    rest = ["--all" if parsed.target == "all" else parsed.target]
    if parsed.dry_run:
        rest.append("--dry-run")
    if parsed.replace:
        rest.append("--replace")
    if parsed.home:
        rest.extend(["--home", parsed.home])
    return rest
