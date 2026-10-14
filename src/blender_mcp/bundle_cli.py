"""Inspect resources embedded in the standalone executable.

Explicit commands only. MCP server startup never prints these diagnostics.
PyInstaller --onefile extracts the data into a temporary directory at runtime;
the original executable remains the only file users have to download and keep.
"""
from __future__ import annotations

import argparse
import json
from importlib import resources
from pathlib import Path
import sys

_PACKAGE = "blender_mcp"
_GUIDES = ("animation", "bpy", "level-design", "materials", "retopology", "rigging", "scene")


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def report() -> dict:
    package = resources.files(_PACKAGE)
    embedded = {
        "addon": package.joinpath("bundled", "addon.py"),
        "skill": package.joinpath("skills", "blender-scene-automation", "SKILL.md"),
        "viewport": package.joinpath("apps", "viewport.html"),
    }
    embedded.update({f"guide:{name}": package.joinpath("guides", f"{name}.md") for name in _GUIDES})
    result = {}
    for label, asset in embedded.items():
        try:
            result[label] = len(asset.read_bytes())
        except (OSError, FileNotFoundError):
            result[label] = 0
    for name, filename in (("license", "LICENSE"), ("documentation", "WINDOWS_BINARY.md")):
        path = _root() / filename
        try:
            result[name] = path.stat().st_size
        except OSError:
            result[name] = 0
    return {
        "status": "ok" if all(value > 100 for value in result.values()) else "error",
        "onefile_runtime": bool(getattr(sys, "frozen", False)),
        "assets": result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp-for-blender.exe bundle")
    parser.add_argument("command", choices=("verify", "license", "docs"))
    parser.add_argument("--json", action="store_true", help="Machine-readable verification output")
    args = parser.parse_args(argv)
    if args.command in ("license", "docs"):
        filename = "LICENSE" if args.command == "license" else "WINDOWS_BINARY.md"
        try:
            print((_root() / filename).read_text(encoding="utf-8"))
        except OSError as error:
            parser.exit(1, f"Bundled {filename} unavailable: {error}\n")
        return 0
    check = report()
    if args.json:
        print(json.dumps(check, indent=2))
    else:
        for name, size in check["assets"].items():
            print(f"{name}: {size} bytes" if size else f"{name}: MISSING")
        print(f"Embedded bundle: {check['status']}; frozen EXE: {check['onefile_runtime']}")
    return 0 if check["status"] == "ok" else 1
