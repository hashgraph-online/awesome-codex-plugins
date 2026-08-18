# CONTAM Plugin

`CONTAM Plugin` is a Windows-first public toolkit for using CONTAM from AI coding agents and MCP-capable desktop tools.

It combines three layers in one repository:

- a local `stdio` MCP server for CONTAM command-line tools and ContamX bridge sessions
- a Codex plugin wrapper with workflow guidance for project creation, diagnosis, and simulation
- guard scripts for PRJ hygiene, ContamW-safe result settings, and optional `contam_chinese` linkage

The project is designed for public use. It helps an agent inspect `.prj` models, diagnose missing references, run simulations, compare outputs, generate simple ContamW SketchPad layouts, and separate solver failures from ContamW GUI result-display problems.

## Quick Use Through MCP

For most users, the easiest setup is an `npx`-launched local MCP server:

```text
command: npx
args: -y --package github:summer521521/CONTAM_plugin contam-mcp
```

The binary name remains `contam-mcp` because it launches the MCP server component. The repository and Codex plugin are named `CONTAM_plugin`.

Host-specific setup examples are in:

- [Host Setup Guide](docs/HOSTS.md)
- [Codex Windows App Setup](docs/CODEX_WINDOWS_APP.md)
- [Five-Minute Quickstart](docs/QUICKSTART.md)

## Codex Plugin Use

This repository can also be used as a Codex plugin source because the repository root contains:

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `skills/contam-mcp/SKILL.md`
- `scripts/start-contam-plugin-mcp.ps1`
- `scripts/Invoke-ContamProjectGuard.ps1`

The plugin adds a CONTAM workflow skill that tells Codex to:

- inspect before editing
- keep case-specific data outside the plugin repository
- run ContamX input checks before GUI work
- keep only one active PRJ in a case folder unless scenarios are intentional
- use GUI-safe output settings when the user will run from ContamW
- record ContamW Building Check errors and fixes in case-local notes

## Main Capabilities

- discover bundled or configured CONTAM executables
- list `.prj`, `.sim`, `.wth`, `.ctm`, and related files
- inspect project metadata and external references
- diagnose broken project references
- update supported `.prj` file references
- clone baseline projects into named scenario folders
- create and optionally run small case matrices
- apply generated ContamW SketchPad layout data for rectangular rooms, zones, path icons, and source/sink icons
- run `contamx3.exe` and collect outputs
- run a PRJ guard for encoding, result profile, stale-output cleanup, XLog triage, and basic count checks
- discover and use optional `contamxpy` bindings for paper-style ContamX API co-simulation
- discover Rhino/Grasshopper ANT availability for model-creation workflows
- upgrade old `.prj` files with `prjup.exe`
- compare `.sim` files with `simcomp.exe`
- export `simread` text output
- summarize generic CONTAM text outputs for quick result triage
- start, inspect, advance, and close ContamX bridge sessions

## Project Guard

Before handing a generated PRJ to another user or asking someone to run it in ContamW, run:

```powershell
.\scripts\Invoke-ContamProjectGuard.ps1 `
  -ProjectPath "<case>\model.prj" `
  -Mode InputCheck `
  -ResultProfile GuiSafeResults `
  -CleanOutputs `
  -RequireSingleProject
```

For a command-line full run:

```powershell
.\scripts\Invoke-ContamProjectGuard.ps1 `
  -ProjectPath "<case>\model.prj" `
  -Mode Run `
  -ResultProfile GuiSafeResults
```

The guard does not prove a hand-drawn SketchPad layout is perfect, but it catches common project-sharing and simulation issues before the GUI step.

## Link With contam_chinese

`CONTAM_plugin` can use the localized executables distributed by [`contam_chinese`](https://github.com/summer521521/contam_chinese).

After extracting a `contam_chinese` release package, link it for the current PowerShell session:

```powershell
.\scripts\link-contam-chinese.ps1 -Path "<extracted-contam-chinese-release>"
```

Or persist it for your Windows user:

```powershell
.\scripts\link-contam-chinese.ps1 -Path "<extracted-contam-chinese-release>" -User
```

The launcher honors these variables in order:

- explicit tool overrides such as `CONTAMX_PATH`
- `CONTAM_HOME`
- `CONTAM_CHINESE_HOME`
- bundled executables in this repository

Use `contam_chinese` for localized ContamW and Chinese help. Use `CONTAM_plugin` for MCP automation, project checks, simulation workflows, and report-oriented result extraction.

## Repository Layout

- `.codex-plugin/`: Codex plugin manifest
- `.mcp.json`: MCP server launch definition for plugin hosts
- `skills/`: Codex workflow skill for CONTAM work
- `scripts/`: launch, guard, localization-link, setup, and maintenance scripts
- `contam-mcp/`: MCP server source, developer guide, and regression scripts
- `docs/`: public quickstart and host setup guides
- `.github/workflows/`: GitHub Actions workflows
- repository root: bundled CONTAM executables and supporting DLLs

## Privacy And CI

This repository includes a privacy check that scans tracked files for personal filesystem paths before public sharing:

```powershell
npm run privacy:check
```

Run the basic plugin launcher check with:

```powershell
npm run plugin:check
```

Run official regression cases with:

```powershell
npm run regression:official
```

## Example Prompts

- `Call discover_contam_installation and confirm CONTAM is available.`
- `List CONTAM case files in this folder.`
- `Inspect this PRJ file and summarize its references and date range.`
- `Run a test input only check for this PRJ.`
- `Make this PRJ safe for ContamW Building Check and result review.`
- `Run this PRJ and list the generated outputs.`
- `Apply a rectangular SketchPad layout to this PRJ so ContamW opens with visible rooms and icons.`
- `Run a small case matrix from this baseline model.`
- `Analyze this CONTAM xlog or simread text export.`
- `Discover whether contamxpy and ANT are available.`
- `Start a CONTAM bridge session for this project.`
- `Advance the active bridge session by 300 seconds and return path flow updates.`

## References

- [contam_chinese](https://github.com/summer521521/contam_chinese)
- [NIST CONTAM Download Page](https://www.nist.gov/el/energy-and-environment-division-73200/nist-multizone-modeling/software/contam/download)
- [NIST CONTAM Software Page](https://www.nist.gov/services-resources/software/contam)
- [NIST TN 1887r1](https://doi.org/10.6028/NIST.TN.1887r1)
- [Model Context Protocol](https://modelcontextprotocol.io/)
