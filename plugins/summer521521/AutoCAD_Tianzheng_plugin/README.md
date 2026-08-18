# AutoCAD Tianzheng Plugin

Public Codex plugin for AutoCAD and Tianzheng HVAC automation through an external autocad_tianzheng MCP server.

This repository is a standalone public Codex plugin package. It contains the plugin manifest, MCP launcher, workflow skills, and lightweight validation scripts. It does not include local software installations, private databases, drawings, simulation artifacts, or machine-specific configuration.

## Requirements

- AutoCAD and Tianzheng installed locally when GUI automation is needed
- External autocad_tianzheng MCP working tree configured with AUTOCAD_TIANZHENG_MCP_ROOT
- Python environment for the MCP server

## Environment

Configure only the variables that apply to your machine:

``powershell
$env:AUTOCAD_TIANZHENG_MCP_ROOT=<path-to-autocad-tianzheng-mcp>
$env:AUTOCAD_TIANZHENG_PYTHON=<optional-python-exe>
$env:AUTOCAD_EXE=<optional-autocad-exe>
$env:TIANZHENG_ROOT=<optional-tianzheng-root>
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
.\scripts\start-autocad-tianzheng-mcp.ps1 -Check
``

## Notes For Contributors

- Do not commit real secrets, local absolute paths, private databases, binary project files, logs, caches, DWG files, Simulink models, or generated simulation outputs.
- Keep machine-specific configuration in environment variables.
- Keep reusable workflow knowledge in skills/ and lightweight scripts in scripts/.

## Source

This standalone repository was split from codex-personal-plugins so it can be used and improved independently.
