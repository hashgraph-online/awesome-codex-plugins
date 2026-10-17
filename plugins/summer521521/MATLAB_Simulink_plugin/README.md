# MATLAB Simulink Plugin

Public Codex plugin for MATLAB MCP Server and Simulink modeling, simulation, baseline testing, and profiler analysis workflows.

This repository is a standalone public Codex plugin package. It contains the plugin manifest, MCP launcher, workflow skills, and lightweight validation scripts. It does not include local software installations, private databases, drawings, simulation artifacts, or machine-specific configuration.

## Requirements

- MATLAB installed locally
- [MATLAB MCP Server](https://github.com/matlab/matlab-mcp-server) v0.11.0 or newer
- MATLAB MCP executable configured with `MATLAB_MCP_EXE` or `MATLAB_MCP_HOME`
- Optional MATLAB_ROOT and MATLAB_INITIAL_WORKING_FOLDER

## Environment

Configure only the variables that apply to your machine:

```powershell
$env:MATLAB_MCP_EXE = "<path-to-matlab-mcp-server-windows-x64.exe>"
# Or point to the folder containing the executable:
$env:MATLAB_MCP_HOME = "<path-to-matlab-mcp-server-folder>"
$env:MATLAB_ROOT = "<path-to-matlab-root>"
$env:MATLAB_INITIAL_WORKING_FOLDER = "<optional-working-folder>"
$env:MATLAB_DISPLAY_MODE = "nodesktop"
```

MATLAB MCP Server v0.11.0 renamed the Windows binary from `matlab-mcp-core-server-win64.exe` to `matlab-mcp-server-windows-x64.exe`. After upgrading, install or update MATLAB MCP Server Toolbox once:

```powershell
& $env:MATLAB_MCP_EXE --setup-matlab "--matlab-root=$env:MATLAB_ROOT"
```

The launcher prefers `MATLAB_MCP_EXE`, can discover the renamed executable from `MATLAB_MCP_HOME`, and retains compatibility with the legacy filename.

## Codex Plugin Layout

- .codex-plugin/plugin.json: plugin manifest
- .mcp.json: MCP server launch definition
- skills/: Codex skills shipped by this plugin
- scripts/: MCP launcher and repository validation scripts

## Local Checks

Run structural and privacy checks before sharing changes:

```powershell
.\scripts\check-plugin.ps1
.\scripts\check-repo-privacy.ps1
```

Run the launcher smoke check after configuring local environment variables:

```powershell
.\scripts\start-matlab-mcp.ps1 -Check
```

## Notes For Contributors

- Do not commit real secrets, local absolute paths, private databases, binary project files, logs, caches, DWG files, Simulink models, or generated simulation outputs.
- Keep machine-specific configuration in environment variables.
- Keep reusable workflow knowledge in skills/ and lightweight scripts in scripts/.

## Source

This standalone repository was split from codex-personal-plugins so it can be used and improved independently.
