"""CLI entry for packaged Windows EXE and Python MCP server."""
import sys

def main():
    args = sys.argv[1:]
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
