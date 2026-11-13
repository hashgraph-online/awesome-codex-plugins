# DESIGN:OS 3D Blender

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/readme/cover-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/readme/cover-light.png">
  <img src="docs/images/readme/cover-dark.png" alt="design:os by Jang" width="100%">
</picture>
</p>

**An MCP server and agent skill for Blender 5.2.** Your coding agent models, renders and checks mechanical parts on your machine: four tools, an `AGENT_OK` contract, and a 3D-print production gate. Specs are locked to millimeters. Exports are STL and glTF.

FREE + source-available ([PolyForm Shield 1.0.0](LICENSE)).

<p>
  <a href="#quickstart">Quickstart</a> · <a href="#what-it-makes">What it makes</a> · <a href="#how-it-works">How it works</a> · <a href="#install">Install</a> · <a href="#limits">Limits</a>
</p>

<p align="left">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-PolyForm_Shield_1.0.0-202020?style=flat-square&labelColor=202020&color=444444" alt="PolyForm Shield 1.0.0 License"></a>
  <a href="https://jangtrinh.github.io/design-os-3d-blender/"><img src="https://img.shields.io/badge/live_docs-GitHub_Pages-202020?style=flat-square&labelColor=202020&color=444444" alt="Live GitHub Pages"></a>
</p>

## Quickstart

**In Claude Code:**

```text
/plugin marketplace add jangtrinh/design-os-3d-blender
/plugin install design-os-3d-blender@design-os-3d-blender
```

**From a clone** (Codex, Gemini CLI, Antigravity, Cursor, or a standalone MCP client):

```bash
git clone https://github.com/jangtrinh/design-os-3d-blender.git
cd design-os-3d-blender
python3 scripts/self_check.py
pip install .
```

Point your MCP client at the installed command, and set `BLENDER_BIN` to your Blender 5.2 binary:

```json
{
  "mcpServers": {
    "design-os-3d-blender": {
      "command": "design-os-3d-blender",
      "env": {
        "BLENDER_BIN": "/Applications/Blender.app/Contents/MacOS/Blender"
      }
    }
  }
}
```

On Linux the binary is often `/usr/bin/blender`. The first tool will tell you if it cannot find it. If you use `uv`, `uv run design-os-3d-blender` from this repository starts the same server, with no need to publish a package.

Ask for a part in plain English. A typical pass validates a `spec.json`, runs a headless bpy script, and stops on one line: `AGENT_OK` or `AGENT_FAIL`.

## What it makes

These are real builds from this repository, made in Blender 5.2 through the agent pipeline.

<p>
  <img src="docs/images/readme/builds/ck-001.jpg" alt="design:os by Jang" width="49%">
  <img src="docs/images/readme/builds/dc-01-exploded.jpg" alt="design:os by Jang" width="49%">
</p>
<p>
  <img src="docs/images/readme/builds/robot-arm.jpg" alt="design:os by Jang" width="49%">
  <img src="docs/images/readme/builds/nodestack.jpg" alt="design:os by Jang" width="49%">
</p>

| Build | What it is | In this repo |
| :--- | :--- | :--- |
| CK-001 | A compact keyboard, from photo and spec to a printable kit | [`docs/reviews/ck-001/r02`](docs/reviews/ck-001/r02) |
| DC-01 | A desk robot: printed parts, a carrier board, an assembly film | [`docs/reviews/dc-01/r03`](docs/reviews/dc-01/r03) |
| Robot arm | A printable arm, with gated plates | [`builds/robot-arm-print-assembly`](builds/robot-arm-print-assembly) |
| Nodestack | Modular industrial storage | [`docs/reviews/nodestack/r03`](docs/reviews/nodestack/r03) |

<p>
  <img src="docs/images/readme/builds/dc-01-assembled.jpg" alt="design:os by Jang" width="49%">
  <img src="docs/images/readme/builds/blender-window.jpg" alt="design:os by Jang" width="49%">
</p>

DC-01 assembled, and the printable robot arm open in a real Blender 5.2 window. Print plates for the arm are in [`docs/images/readme/builds/print-plates.jpg`](docs/images/readme/builds/print-plates.jpg) and [`docs/media/robot-arm-print-plates.png`](docs/media/robot-arm-print-plates.png).

## How it works

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/readme/flow-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/readme/flow-light.png">
  <img src="docs/images/readme/flow-dark.png" alt="design:os by Jang" width="100%">
</picture>
</p>

The MCP server exposes **four tools**. That is the count in `src/design_os_3d_blender_mcp/server.py` on this branch:

| Tool | What it does |
| :--- | :--- |
| `blender_runtime_status` | Host, Python, and whether a Blender 5.2 binary is on the path. Call this first. |
| `query_blender_knowledge` | Search the verified bpy 5.2 knowledge base in `knowledge/` before writing a script. |
| `validate_part_spec` | Check a `spec.json`: units in mm, target dimensions, tolerance, minimum wall. |
| `execute_blender_pass` | Run a headless pass and read the `AGENT_OK` or `AGENT_FAIL` line. |

Two prompts (`design_parametric_part`, `review_geometry_gate`) and two resources (`blender://knowledge/index`, `blender://specs/bracket-example`) sit next to the tools. They are not extra tools.

Every executed pass ends with one machine-readable line. Exit codes alone are not a verdict. The 3D-print production gate checks manifold geometry, wall thickness and millimeter-locked bounds. Worked specs live in `specs/` and `builds/`.

The Claude Code, Codex and other agent plugins install the same skill, [`skills/design-os-3d-blender/SKILL.md`](skills/design-os-3d-blender/SKILL.md). `/doctor` is a read-only diagnostic. `python3 scripts/self_check.py` is the offline repository check: it prints `ok: design-os-3d-blender self-check passed (design-os-3d-blender)` and exits 0 when the manifests and contracts match.

Nothing in the server sends data off your machine. See [`PRIVACY.md`](PRIVACY.md).

## Install

Choose the setup that matches your agent. Every option uses the same skill at `skills/design-os-3d-blender/SKILL.md`.

### Claude Code

```text
/plugin marketplace add jangtrinh/design-os-3d-blender
/plugin install design-os-3d-blender@design-os-3d-blender
```

### OpenAI Codex

```bash
git clone https://github.com/jangtrinh/design-os-3d-blender.git /tmp/design-os-3d-blender
mkdir -p ~/.codex/skills/design-os-3d-blender ~/.codex/prompts
cp -R /tmp/design-os-3d-blender/skills/design-os-3d-blender/* ~/.codex/skills/design-os-3d-blender/
cp /tmp/design-os-3d-blender/prompts/doctor.md ~/.codex/prompts/design-os-3d-blender-doctor.md
rm -rf /tmp/design-os-3d-blender
```

### Gemini CLI and Google Antigravity

```bash
git clone https://github.com/jangtrinh/design-os-3d-blender.git /tmp/design-os-3d-blender
mkdir -p ~/.gemini/skills/design-os-3d-blender
cp -R /tmp/design-os-3d-blender/skills/design-os-3d-blender/* ~/.gemini/skills/design-os-3d-blender/
rm -rf /tmp/design-os-3d-blender
```

### OpenCode, Cursor, Windsurf and other agent harnesses

```bash
git clone https://github.com/jangtrinh/design-os-3d-blender.git /tmp/design-os-3d-blender
mkdir -p ~/.agents/skills/design-os-3d-blender
cp -R /tmp/design-os-3d-blender/skills/design-os-3d-blender/* ~/.agents/skills/design-os-3d-blender/
rm -rf /tmp/design-os-3d-blender
```

<details>
<summary>Verify or uninstall</summary>

**Verify:**

```bash
python3 scripts/self_check.py
```

Or run `/doctor` inside Claude Code or Codex to inspect installed skill paths, plugin manifests, and whether Blender is reachable.

**Uninstall the skill copies:**

```bash
rm -rf ~/.claude/skills/design-os-3d-blender ~/.codex/skills/design-os-3d-blender ~/.gemini/skills/design-os-3d-blender ~/.agents/skills/design-os-3d-blender
```

</details>

Prompt recipes live in [`docs/cookbook.md`](docs/cookbook.md). More setup notes are in [`docs/antigravity-setup.md`](docs/antigravity-setup.md) and [`docs/upstream-agent-integration.md`](docs/upstream-agent-integration.md).

## Limits

- Sheet-metal or paperboard folding, where 2D crease patterns govern the topology: use [`design-os-origami`](https://github.com/jangtrinh/design-os-origami).
- Organic character sculpting or a full game-character rig that needs a sculptor's pass.
- 2D vector UI motion: use [`design-os-svg-animation`](https://github.com/jangtrinh/design-os-svg-animation).

## Watch

A FREE, source-available (PolyForm Shield) agent pipeline for Blender 5.2. Videos from the [design:os by Jang](https://www.youtube.com/@designosbyjang) channel (Vietnamese, with English terms):

<p align="left">
  <a href="https://www.youtube.com/watch?v=J2Malrlb_PM"><img src="docs/images/video/J2Malrlb_PM.jpg" alt="design:os by Jang" width="320"></a>
  <a href="https://www.youtube.com/watch?v=LKL7ZHMz5KI"><img src="docs/images/video/LKL7ZHMz5KI.jpg" alt="design:os by Jang" width="320"></a>
  <a href="https://www.youtube.com/watch?v=XSKZYudfMt8"><img src="docs/images/video/XSKZYudfMt8.jpg" alt="design:os by Jang" width="320"></a>
</p>

- [How to use design os 3d blender repo - ep 1](https://www.youtube.com/watch?v=J2Malrlb_PM) (2:57). Episode 1: building a keyboard (CK-001) end to end: photo, spec, gates, STL and GLB export. Vietnamese.
- [How to use design os 3d blender repo - ep 2](https://www.youtube.com/watch?v=LKL7ZHMz5KI) (5:34). Episode 2: the DC-01 desk robot with 29 mechanical revisions, four gated runs and a printable kit. Vietnamese.
- [Fanmade 3D model for Nowa planet - by design os 3d blender](https://www.youtube.com/watch?v=XSKZYudfMt8) (0:27). A 27-second fan-made 3D model of the Nowa desktop product, built with design-os-3d-blender.

More: [design:os by Jang on YouTube](https://www.youtube.com/@designosbyjang).

## DESIGN:OS

This is one of the DESIGN:OS tools. The others: [Studio](https://github.com/jangtrinh/design-os-studio), [CLI](https://github.com/jangtrinh/design-os), [Bridge](https://github.com/jangtrinh/design-os-figma-plugin), [SVG Animation](https://github.com/jangtrinh/design-os-svg-animation), [Code2Flow](https://github.com/jangtrinh/design-os-code2flow), [Knowledge Builder](https://github.com/jangtrinh/design-os-knowledge-builder) and more on [jangtrinh.github.io](https://jangtrinh.github.io/).

| Engine | Live docs | Repository |
| :--- | :--- | :--- |
| DESIGN:OS CLI | [jangtrinh.github.io/design-os](https://jangtrinh.github.io/design-os/) | [`jangtrinh/design-os`](https://github.com/jangtrinh/design-os) |
| Knowledge Builder | [jangtrinh.github.io/design-os-knowledge-builder](https://jangtrinh.github.io/design-os-knowledge-builder/) | [`jangtrinh/design-os-knowledge-builder`](https://github.com/jangtrinh/design-os-knowledge-builder) |
| DESIGN:OS Bridge | [jangtrinh.github.io/design-os-figma-plugin](https://jangtrinh.github.io/design-os-figma-plugin/) | [`jangtrinh/design-os-figma-plugin`](https://github.com/jangtrinh/design-os-figma-plugin) |
| SVG Animation Engine | [jangtrinh.github.io/design-os-svg-animation](https://jangtrinh.github.io/design-os-svg-animation/) | [`jangtrinh/design-os-svg-animation`](https://github.com/jangtrinh/design-os-svg-animation) |
| 3D Blender | [jangtrinh.github.io/design-os-3d-blender](https://jangtrinh.github.io/design-os-3d-blender/) | [`jangtrinh/design-os-3d-blender`](https://github.com/jangtrinh/design-os-3d-blender) |
| OPAH ONE Drone | [jangtrinh.github.io/design-os-drone-showcase](https://jangtrinh.github.io/design-os-drone-showcase/) | [`jangtrinh/design-os-drone-showcase`](https://github.com/jangtrinh/design-os-drone-showcase) |
| GitHub Pages Engine | [jangtrinh.github.io/design-os-github-page](https://jangtrinh.github.io/design-os-github-page/) | [`jangtrinh/design-os-github-page`](https://github.com/jangtrinh/design-os-github-page) |
| Apple Design OS | [jangtrinh.github.io/design-os-apple](https://jangtrinh.github.io/design-os-apple/) | [`jangtrinh/design-os-apple`](https://github.com/jangtrinh/design-os-apple) |
| Agent Teacher | [jangtrinh.github.io/design-os-pedagogy](https://jangtrinh.github.io/design-os-pedagogy/) | [`jangtrinh/design-os-pedagogy`](https://github.com/jangtrinh/design-os-pedagogy) |
| Origami CAD | [jangtrinh.github.io/design-os-origami](https://jangtrinh.github.io/design-os-origami/) | [`jangtrinh/design-os-origami`](https://github.com/jangtrinh/design-os-origami) |
| Voice UX Architecture | [jangtrinh.github.io/design-os-voice-ux](https://jangtrinh.github.io/design-os-voice-ux/) | [`jangtrinh/design-os-voice-ux`](https://github.com/jangtrinh/design-os-voice-ux) |
| Code2Flow | [jangtrinh.github.io/design-os-code2flow](https://jangtrinh.github.io/design-os-code2flow/) | [`jangtrinh/design-os-code2flow`](https://github.com/jangtrinh/design-os-code2flow) |
| Generative UI | [jangtrinh.github.io/design-os-generative-ui](https://jangtrinh.github.io/design-os-generative-ui/) | [`jangtrinh/design-os-generative-ui`](https://github.com/jangtrinh/design-os-generative-ui) |

Docs: [jangtrinh.github.io/design-os-3d-blender](https://jangtrinh.github.io/design-os-3d-blender/) · Changelog: [`CHANGELOG.md`](CHANGELOG.md) · Index for AI agents: [`llms.txt`](llms.txt)

## Contributing and license

- [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`SECURITY.md`](SECURITY.md) · [`PRIVACY.md`](PRIVACY.md)
- [PolyForm Shield 1.0.0](LICENSE). FREE to use and modify, including for paid client work; you may not resell it or build a competing product from it.

## Built by

Built by [Jang Trịnh](https://github.com/jangtrinh), creative technologist and autonomous system architect. More projects, case studies and writing at [jang.work](https://www.jang.work/?utm_source=github&utm_medium=readme&utm_campaign=design-os-3d-blender).

[GitHub](https://github.com/jangtrinh) · [LinkedIn](https://www.linkedin.com/in/jangtrinh/) · [Hub](https://jangtrinh.github.io/) · [YouTube](https://www.youtube.com/@designosbyjang) · [X](https://x.com/Jangtrinhvn)

## Listed on

<p align="left">
  <a href="https://mcpservers.org/servers/jangtrinh/design-os-3d-blender"><img src="https://mcpservers.org/badge.svg" alt="Listed on mcpservers.org" width="163" height="20"></a>
  <a href="https://aiagentsdirectory.com?utm_source=badge&utm_medium=referral&utm_campaign=free_listing&utm_content=homepage"><img src="https://aiagentsdirectory.com/featured-badge.svg?v=2024" alt="Featured AI Agents on AI Agents Directory" width="160" height="40"></a>
</p>

Also listed in the [Official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=design-os-3d-blender) (`io.github.jangtrinh/design-os-3d-blender`), the [awesome-mcp-servers list by TensorBlock](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/art-culture--media.md) and [SkillsMP](https://skillsmp.com/creators/jangtrinh).

If `design-os-3d-blender` saves you time, a star on GitHub helps other engineers and AI agents find it.

<p align="left">
  <a href="https://buymeacoffee.com/jangtrinh">
    <img src="https://img.shields.io/badge/Buy_Me_a_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee">
  </a>
</p>
