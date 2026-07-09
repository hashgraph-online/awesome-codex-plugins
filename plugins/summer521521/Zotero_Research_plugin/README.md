# Zotero Research Plugin

Public Codex plugin for searching, reading, summarizing, citing, and organizing Zotero library items through Zotero MCP.

This repository is a standalone public Codex plugin package. It contains the plugin manifest, MCP launcher, workflow skills, and lightweight validation scripts. It does not include local software installations, private databases, drawings, simulation artifacts, or machine-specific configuration.

## Requirements

- Zotero desktop installed locally
- zotero-mcp available on PATH or configured with ZOTERO_MCP_EXE
- Optional ZOTERO_DB_PATH for explicit local database access

## Environment

Configure only the variables that apply to your machine:

``powershell
$env:ZOTERO_MCP_EXE=<optional-path-to-zotero-mcp>
$env:ZOTERO_DB_PATH=<optional-path-to-zotero.sqlite>
$env:ZOTERO_LOCAL=true
$env:ZOTERO_NO_CLAUDE=true
``

## Codex Plugin Layout

- .codex-plugin/plugin.json: plugin manifest
- .mcp.json: MCP server launch definition
- skills/: Codex skills shipped by this plugin
- scripts/: MCP launcher and repository validation scripts

## Local Checks

Run structural and privacy checks before sharing changes:

``powershell
.\scripts\check-plugin.ps1
.\scripts\check-repo-privacy.ps1
``

Run the launcher smoke check after configuring local environment variables:

``powershell
.\scripts\start-zotero-mcp.ps1 -Check
``

## Notes For Contributors

- Do not commit real secrets, local absolute paths, private databases, binary project files, logs, caches, DWG files, Simulink models, or generated simulation outputs.
- Keep machine-specific configuration in environment variables.
- Keep reusable workflow knowledge in skills/ and lightweight scripts in scripts/.

## Source

This standalone repository was split from codex-personal-plugins so it can be used and improved independently.
