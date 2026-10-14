---
name: blender-scene-automation
description: Model, edit, inspect, shade, light, render, animate and export Blender scenes through the local Blender MCP server with safe Python and visual verification.
---

# Blender scene automation (MCP for Blender)

The AI client performs planning; the **blender** MCP server talks to the running Blender desktop application's addon.

## Connect

1. Open Blender and enable the "MCP for Blender" addon. Press N in the 3D viewport, find the MCP tab and start the socket server if necessary.
2. Call `get_addon_status` then `get_scene_info`. Discover tool names from the active server rather than inventing them.
3. If the addon is missing, explicitly run `mcp-for-blender.exe install-addon`, enable it in Blender preferences, and restart Blender.
4. If the MCP connection fails, describe the error; do not claim objects were created.

## Inspect → plan → edit → verify

1. Inspect objects, collections, modifiers, materials, units, camera and render settings. Use `look` to examine the viewport.
2. Work in small stages: blockout, geometry, materials, lighting, camera, preview render, final output.
3. Use `execute_blender_code` for targeted `bpy` scripts. Avoid scene-wide destructive operations and preserve object names/links.
4. After meaningful operations, inspect with `get_scene_info` or `look`. Verify rendered output rather than trusting execution alone.
5. Save the `.blend` project and requested exported assets; distinguish verified results from untested assumptions.

## bpy and modeling tips

- Find nodes by type (for example `BSDF_PRINCIPLED`), not translated names. For rendered colors use shader node sockets rather than `material.diffuse_color` alone.
- Inspect valid enums before changing render engines or version-specific settings.
- Prefer `bpy.data` where Blender operator context is unreliable; set mode and active object explicitly if an operator is necessary.
- Validate units, scale, bounding boxes, normals, geometry and object/material links.
- Use `get_guide` for procedural modeling, materials, animation, rigging or retopology where available.
- Asset search/import can introduce arbitrary scale. AI `generate_3d` may consume paid credits or transmit data to an external provider; ask for approval.

## Safety

- `execute_blender_code` runs arbitrary local Python code in Blender. Never read unrelated files, secrets, external URLs or run a shell command without explicit authorization.
- Ask before deleting objects, replacing active projects, overwriting files, expensive renders and paid external generation.
- Prefer nondestructive changes and save a backup of valuable scenes. Never fabricate tool results.
