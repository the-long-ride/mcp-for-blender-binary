"""Windows one-file executable entry point and MCP stdio launcher."""
import sys


def main():
    args = sys.argv[1:]

    # Only reconfigure CLI streams: MCP stdio must be completely unaltered.
    # PowerShell may use cp1252 for redirected stdout, while docs and Blender
    # messages contain Unicode. Unsupported characters are escaped, not fatal.
    cli_command = bool(args) and (
        args[0] in {"bundle", "install", "install-addon", "addon-paths",
                    "setup", "update", "agents", "help", "--help", "-h"}
        or "-h" in args or "--help" in args
    )
    if cli_command:
        for stream in (sys.stdout, sys.stderr):
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(errors="backslashreplace")

    # The empty command is deliberately *not* help: clients launch the EXE
    # with zero arguments and exchange MCP JSON-RPC over stdout.
    if args and (args[0] == "help" or "-h" in args or "--help" in args):
        from blender_mcp.cli_help import print_help_for
        if args[0] == "help":
            return print_help_for([*args[1:], "--help"])
        return print_help_for(args)

    if args and args[0] == "bundle":
        from blender_mcp.bundle_cli import main as bundle_main
        return bundle_main(args[1:])
    if args and args[0] == "install":
        from blender_mcp.installer import main as install_main
        return install_main(args[1:])
    if args and args[0] == "agents":
        from blender_mcp.cli_help import agent_install_arguments
        from blender_mcp.installer import main as install_main
        rest = agent_install_arguments(args[1:])
        return install_main(rest)

    from blender_mcp.server import main as server_main
    return server_main()


if __name__ == "__main__":
    sys.exit(main() or 0)
