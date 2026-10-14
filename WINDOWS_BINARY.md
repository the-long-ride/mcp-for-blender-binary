# Standalone Windows EXE for MCP for Blender

This fork distributes **one file: `mcp-for-blender.exe`**, built with PyInstaller.
The executable embeds the Python runtime and MCP dependencies, Blender addon,
viewport UI, built-in guides, AI-agent skill, MCP/agent instruction installer,
license and documentation. No companion files, Python, Node.js or uv are
required on the user's Windows computer.

**Blender and your chosen AI agent are separate applications** and must already
be installed. The EXE talks to Blender through its addon; it does not bundle
the Blender application itself.

## Download

Go to GitHub Actions → **Build Windows standalone EXE (Node.js 24)** → **Run workflow**.
Download the successful `mcp-for-blender-windows-exe` artifact. GitHub Actions
delivers artifacts in a ZIP; extract it to find the **single**
`mcp-for-blender.exe` file. Move the EXE to a permanent directory *before*
installing MCP registrations because they reference its absolute path.

## Install for one AI agent

Open PowerShell in the folder containing the EXE and choose **one** command:

```powershell
.\mcp-for-blender.exe install codex
.\mcp-for-blender.exe install claude
.\mcp-for-blender.exe install antigravity
.\mcp-for-blender.exe install opencode
```

Each command installs **only the selected agent's** MCP registration, skill and
agent instructions (and the shared canonical skill at
`~/.agents/skills/blender-scene-automation/SKILL.md`).

Alternatively, configure every supported AI client:

```powershell
.\mcp-for-blender.exe install --all
```

Optional `install claude-desktop` configures Claude Desktop separately;
`claude-code` aliases `claude`, and `chatgpt` aliases `codex`.

The equivalent explicit target syntax is:

```powershell
.\mcp-for-blender.exe agents install --target codex
.\mcp-for-blender.exe agents install --target all
```

Preview and replacement options:

```powershell
.\mcp-for-blender.exe install codex --dry-run
.\mcp-for-blender.exe install codex --replace
```

Existing unrelated configurations and global instructions are preserved.
The installer writes backups of changed existing files and does not overwrite
an existing `blender` MCP entry unless `--replace` is specified. It rejects
malformed JSON/TOML instead of overwriting it and is safe to rerun.

## Help for every command

Use the root help to discover the command tree or request help for a
specific command or AI agent:

```powershell
.\mcp-for-blender.exe --help
.\mcp-for-blender.exe install --help
.\mcp-for-blender.exe install codex --help
.\mcp-for-blender.exe install claude --help
.\mcp-for-blender.exe install antigravity --help
.\mcp-for-blender.exe install opencode --help
.\mcp-for-blender.exe agents --help
.\mcp-for-blender.exe agents install --help
.\mcp-for-blender.exe bundle --help
.\mcp-for-blender.exe bundle verify --help
.\mcp-for-blender.exe install-addon --help
```

The `bundle license`, `bundle docs`, `addon-paths`, `setup` and `update`
commands also support `--help`. Running `mcp-for-blender.exe` without any
arguments starts the MCP **stdio server** and never runs installation or prints
help on the JSON-RPC output stream.

## Installation locations

| Client | MCP registration | Agent instructions | Skill copy |
| --- | --- | --- | --- |
| Codex / ChatGPT Codex | `~/.codex/config.toml` | `~/.codex/AGENTS.md` | `~/.agents/skills/blender-scene-automation/SKILL.md` |
| Claude Code | `~/.claude.json` | `~/.claude/CLAUDE.md` | `~/.claude/skills/blender-scene-automation/SKILL.md` |
| Antigravity | `~/.gemini/config/mcp_config.json` | `~/.gemini/GEMINI.md` | `~/.gemini/config/skills/blender-scene-automation/SKILL.md` |
| OpenCode | `~/.config/opencode/opencode.json` | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/skills/blender-scene-automation/SKILL.md` |

Every selected agent also receives the shared skill under `~/.agents/skills`.
The Antigravity CLI receives an additional skill copy under
`~/.gemini/antigravity-cli/skills/`.

## Install the bundled Blender addon

This is independent of client selection. The addon is embedded in the EXE, so
no downloaded `addon.py` is needed:

```powershell
.\mcp-for-blender.exe install-addon
```

Enable **MCP for Blender** in Blender Preferences → Add-ons. In the viewport
press **N**, open the MCP for Blender panel and start the addon server when needed.
Restart the selected AI agent after installing its MCP registration and skill.

## Verify the one-file binary

```powershell
.\mcp-for-blender.exe bundle verify
.\mcp-for-blender.exe bundle docs
.\mcp-for-blender.exe bundle license
```

The workflow uses `actions/checkout@v6`, `actions/setup-node@v6` with Node.js
24, `actions/setup-python@v6` and `actions/upload-artifact@v6`.
Python 3.11 is embedded through PyInstaller. The build is a **console** EXE
because MCP uses stdio.

CI validates installer regression tests, CLI help for each command and client,
single-file packaging and relocation without sidecars, embedded resources,
addon installation with content hash comparison, selected-agent installations,
and MCP initialize/tools-list over real frozen EXE stdio.

**Limitations:** CI does not exercise a live Blender GUI or installed AI
clients. The EXE is unsigned and may trigger Windows SmartScreen. Executing
Blender code through MCP has the privileges of local Python, so review
destructive or otherwise sensitive actions before approving them.
