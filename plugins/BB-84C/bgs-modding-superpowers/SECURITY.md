# Security Policy

## Reporting a Vulnerability

If you discover a security issue in the bundled bgs-modding-superpowers plugin (MCP servers, MO2 control-plane broker, skills, or supporting scripts), please open a private security advisory on the upstream repository:

https://github.com/BB-84C/bgs-modding-superpowers/security/advisories/new

For non-sensitive issues, a regular GitHub issue on the upstream repository is fine:

https://github.com/BB-84C/bgs-modding-superpowers/issues

Please include:

- Affected version (`.codex-plugin/plugin.json` `version` field)
- Reproduction steps
- Affected component (xEdit MCP, bgs-kb MCP, MO2 MCP, MO2 control-plane broker, or specific skill)
- Expected vs observed behavior

## Scope

In scope:

- The bundled MCP servers (`tools/xedit-mcp`, `tools/bgs-kb-mcp`, `tools/mo2-mcp`)
- The MO2 control-plane Python broker (`tools/mo2-control-plane/live-bridge/`)
- The Skills shipped in `skills/`
- Distribution scripts under `scripts/`

Out of scope:

- Bugs in user-installed Bethesda mods, MO2 itself, or xEdit upstream
- Misuse of the toolkit to mutate game files outside the documented MO2 overlay seam (the toolkit refuses by default)
