"""CLI entry for packaged Windows EXE and Python MCP server."""
import sys

def main():
    args = sys.argv[1:]
    # Windows stdout may default to cp1252 when a CLI is invoked from a
    # redirected PowerShell process. The embedded docs and Blender addon
    # messages contain Unicode; escape unsupported codepoints rather than
    # aborting an otherwise successful install. Do not touch MCP stdio.
    cli_command = bool(args) and (
        args[0] in {"bundle", "install", "install-addon", "addon-paths",
                    "setup", "update", "--help", "-h"}
        or args[:2] == ["agents", "install"]
    )
    if cli_command:
        for stream in (sys.stdout, sys.stderr):
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(errors="backslashreplace")
    if args and args[0] == "bundle":
        from blender_mcp.bundle_cli import main as bundle_main
        return bundle_main(args[1:])
    if args and args[0] == "install":
        from blender_mcp.installer import main as install_main
        return install_main(args[1:])
    if args[:2] == ["agents", "install"]:
        from blender_mcp.installer import main as install_main
        rest = args[2:]
        if len(rest) >= 2 and rest[0] == "--target":
            rest = (["--all"] if rest[1] == "all" else [rest[1]]) + rest[2:]
        return install_main(rest)
    from blender_mcp.server import main as server_main
    return server_main()

if __name__ == "__main__":
    sys.exit(main() or 0)
