# Standalone Windows EXE for MCP for Blender

This fork packages the Python MCP server into a **single Windows console executable**
`mcp-for-blender.exe` with PyInstaller. **The downloadable workflow artifact contains only\n`mcp-for-blender.exe`, with no required sidecar files.** The executable embeds\nthe Blender addon, the full Python MCP server and dependencies, built-in guides,\nviewport UI HTML, an AI-agent skill, the agent installer, documentation and license. No Python, uv,
Node.js or agent CLI is required on the end-user machine. **Blender itself must
still be installed.** Node.js 24 is used by CI to verify the MCP protocol.

## Download and install

On GitHub, choose **Actions → Build Windows standalone EXE (Node.js 24) → Run
workflow**. Download/extract the `mcp-for-blender-windows-exe` artifact from a
successful run. Extract the ZIP (GitHub Actions always downloads artifacts as\na ZIP); inside it is **one file: `mcp-for-blender.exe`**. Move the EXE into a\n**permanent directory** before
registering it: MCP client configurations point to its absolute path.

In PowerShell from the directory containing the EXE:

```powershell
.\mcp-for-blender.exe install --all
```

Or target a specific AI client:

```powershell
.\mcp-for-blender.exe install codex
.\mcp-for-blender.exe install claude
.\mcp-for-blender.exe install antigravity
.\mcp-for-blender.exe install opencode
.\mcp-for-blender.exe install --all --dry-run
.\mcp-for-blender.exe install --all --replace
.\mcp-for-blender.exe agents install --target all
```

The installer is optional and does not run when the binary starts as a regular
MCP stdio server. It does not require installed Codex/Claude/OpenCode CLIs.
It merges existing config files and agent instructions, creates backup
`.bak` files for changed existing files, refuses malformed JSON or TOML,
and preserves pre-existing `blender` MCP entries unless `--replace` is provided.
Installing again is idempotent. The Blender addon and skills are installed\n**from the EXE itself**, not downloaded separately.

## Configuration locations

| Agent | MCP registration | Global instructions | Skill copy |
|---|---|---|---|
| Codex | `~/.codex/config.toml` | `~/.codex/AGENTS.md` | `~/.agents/skills/blender-scene-automation/SKILL.md` |
| Claude Code | `~/.claude.json` | `~/.claude/CLAUDE.md` | `~/.claude/skills/blender-scene-automation/SKILL.md` |
| Antigravity | `~/.gemini/config/mcp_config.json` | `~/.gemini/GEMINI.md` | `~/.gemini/config/skills/blender-scene-automation/SKILL.md` |
| OpenCode | `~/.config/opencode/opencode.json` | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/skills/blender-scene-automation/SKILL.md` |

**Every selected client also gets the shared skill at**
`~/.agents/skills/blender-scene-automation/SKILL.md`.
Antigravity CLI additionally receives its own skill copy. Optional
`install claude-desktop` uses the Claude Desktop app config without adding
developer-agent instructions. The `chatgpt` alias targets Codex.

## Blender addon and first run

Install the Blender addon directly from the same executable (no `addon.py`\nsidecar or network download is needed):

```powershell
.\mcp-for-blender.exe install-addon
```

Then enable **MCP for Blender** in Blender Preferences → Add-ons.
In the viewport press **N**, find the MCP for Blender panel and start the
addon socket server if it is not running. Restart the chosen AI client and ask
it to inspect the current scene.

No user-provided LLM key is required by the MCP bridge itself. External asset
generation services may require their own keys, payment or approval.

## Build and validation

`.github/workflows/windows-exe.yml` supports manual dispatch, relevant PR
changes and `v*` tags. It uses `actions/checkout@v6`,
`actions/setup-node@v6` with Node.js **24**, `actions/setup-python@v6`
and `actions/upload-artifact@v6`. Python 3.11 is embedded by PyInstaller.
The build remains a **console** executable because stdio is required by MCP.

CI tests installer behavior, the packaged installer and the frozen server's
MCP `initialize` and `tools/list` protocol. The uploaded artifact includes
the binary, license, skill, build dependency list and SHA-256 checksum.

CI does not validate live communication with Blender's GUI or real AI client
sessions. Windows may warn about the unsigned EXE. Treat this build as
unverified until a successful workflow run and its artifacts are inspected.

**Security:** The MCP server can execute Python inside Blender. Do not accept
untrusted code or authorize destructive scene changes without review.
