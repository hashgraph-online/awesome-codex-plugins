# DESIGN:OS SVG Animation

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/readme/cover-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/readme/cover-light.png">
  <img src="docs/images/readme/cover-dark.png" alt="design:os by Jang" width="100%">
</picture>
</p>

A deterministic vector animation pipeline for coding agents. Motion is authored as a motion IR, quantized on a virtual clock, and exported at 1920×1080 and 60 fps (`scripts/export-player-deliverable.mjs` sets `fps: 60`; export scripts use a 1920×1080 viewport). The same pipeline also writes 9:16 and 1:1 frames.

Eleven Anti-Flop gates, numbered 0 to 10, live in `scripts/anti-flop-gate.py`. Package version 0.1.0, from `package.json`. The canonical skill is `skills/line-art-motion/SKILL.md`.

FREE + source-available ([PolyForm Shield 1.0.0](LICENSE)). It runs locally and works with Claude Code, Codex, Gemini CLI and Antigravity.

<p>
  <a href="#quickstart">Quickstart</a> · <a href="#what-it-makes">What it makes</a> · <a href="#how-it-works">How it works</a> · <a href="#install-for-your-agent">Install</a> · <a href="#limits">Limits</a>
</p>

## Quickstart

**In Claude Code:**

```text
/plugin marketplace add jangtrinh/design-os-svg-animation
/plugin install design-os-svg-animation@design-os-svg-animation
```

**From a clone** (Codex, Gemini CLI, Antigravity, OpenCode, or a plain shell):

```bash
git clone https://github.com/jangtrinh/design-os-svg-animation.git
cd design-os-svg-animation
python3 scripts/anti-flop-gate.py
python3 scripts/self_check.py
```

Ask your agent for a 60 fps walkthrough, a compiled HTML player, or a check that cursor click hotspots sit within 1.0 px of their targets.

## What it makes

These are real films and players from this repository, not mocks.

<p>
<a href="docs/promo/dc-01-tutorial/dc-01-tutorial-landscape.mp4"><img src="docs/assets/example-9-dc-01-tutorial.gif" alt="design:os by Jang" width="100%"></a>
</p>

Tutorials built with the engine: [DC-01 desk robot, 5:34](docs/promo/dc-01-tutorial/dc-01-tutorial-landscape.mp4) ([9:16](docs/promo/dc-01-tutorial/dc-01-tutorial-portrait.mp4)), [CK-001 keyboard, 2:57](docs/promo/ck-001-tutorial/ck-001-tutorial-landscape.mp4) ([9:16](docs/promo/ck-001-tutorial/ck-001-tutorial-portrait.mp4)), [DESIGN:OS 3D Blender promo, 30 s](docs/promo/design-os-3d-blender/design-os-3d-blender-promo-landscape.mp4) ([9:16](docs/promo/design-os-3d-blender/design-os-3d-blender-promo-portrait.mp4)). Workflow: [docs/tutorial-video-workflow.md](docs/tutorial-video-workflow.md).

<p>
<a href="docs/promo/origami-cad/origami-cad-promo.mp4"><img src="docs/assets/example-5-origami-cad-promo.gif" alt="design:os by Jang" width="100%"></a>
</p>

[DESIGN:OS Origami CAD promo, 1080p 60 fps MP4](docs/promo/origami-cad/origami-cad-promo.mp4) · [HTML player](docs/promo/origami-cad/origami-cad-promo.html).

Interactive suites already in the repo:

| Suite | Playground | Cover |
| :--- | :--- | :--- |
| Grade 1 Math (25 figures) | [docs/playground/math-grade1.html](docs/playground/math-grade1.html) | [docs/assets/math-gallery-cover.png](docs/assets/math-gallery-cover.png) |
| Physics Mechanics | [docs/playground/physics.html](docs/playground/physics.html) | [docs/assets/physics-gallery-cover.png](docs/assets/physics-gallery-cover.png) |
| Chemistry Reactions | [docs/playground/chemistry.html](docs/playground/chemistry.html) | [docs/assets/chemistry-gallery-cover.png](docs/assets/chemistry-gallery-cover.png) |
| Physical Education Kinematics | [docs/playground/pe.html](docs/playground/pe.html) | [docs/assets/pe-gallery-cover.png](docs/assets/pe-gallery-cover.png) |

A Universal StudioPlayer HTML file, a validated motion IR timeline, and an MP4 or WebM showreel are the usual outputs. Gate 9 checks the player. Gates 5 to 8 check the IR, hotspots and the virtual clock. Gate 10 checks the showreel.

## How it works

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/readme/flow-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/readme/flow-light.png">
  <img src="docs/images/readme/flow-dark.png" alt="design:os by Jang" width="100%">
</picture>
</p>

Your agent loads `skills/line-art-motion/SKILL.md`. The motion IR is compiled locally. `python3 scripts/anti-flop-gate.py` runs gates 0 to 10. `python3 scripts/self_check.py` and `/doctor` check the install. Nothing is sent off your machine to render a frame.

## Install for your agent

Every option installs the same skill, `skills/line-art-motion/SKILL.md`.

**Claude Code:** the two `/plugin` commands in Quickstart.

**Codex**

```bash
git clone https://github.com/jangtrinh/design-os-svg-animation.git /tmp/design-os-svg-animation
mkdir -p ~/.codex/skills/line-art-motion ~/.codex/prompts
cp -R /tmp/design-os-svg-animation/skills/line-art-motion/* ~/.codex/skills/line-art-motion/
cp /tmp/design-os-svg-animation/prompts/doctor.md ~/.codex/prompts/line-art-motion-doctor.md
rm -rf /tmp/design-os-svg-animation
```

**Gemini CLI and Antigravity**

```bash
git clone https://github.com/jangtrinh/design-os-svg-animation.git /tmp/design-os-svg-animation
mkdir -p ~/.gemini/skills/line-art-motion
cp -R /tmp/design-os-svg-animation/skills/line-art-motion/* ~/.gemini/skills/line-art-motion/
rm -rf /tmp/design-os-svg-animation
```

**OpenCode, Cursor, Windsurf and other harnesses**

```bash
git clone https://github.com/jangtrinh/design-os-svg-animation.git /tmp/design-os-svg-animation
mkdir -p ~/.agents/skills/line-art-motion
cp -R /tmp/design-os-svg-animation/skills/line-art-motion/* ~/.agents/skills/line-art-motion/
rm -rf /tmp/design-os-svg-animation
```

Recipes: [docs/cookbook.md](docs/cookbook.md). Tutorial film workflow: [docs/tutorial-video-workflow.md](docs/tutorial-video-workflow.md).

## Commands

| Command | Where | What it does |
| :--- | :--- | :--- |
| `/doctor` | Claude Code or Codex | Read-only check of skill paths, plugin manifests and prerequisites |
| `python3 scripts/self_check.py` | Terminal or CI | Offline check of manifests, skill contracts and governance files |
| `python3 scripts/anti-flop-gate.py` | Terminal or CI | Run all eleven Anti-Flop gates (gate 0 through gate 10) |

## Limits

Use this when you want frame-exact vector motion, a virtual clock, and a file you can check. It is not a general video editor, and it does not replace a live motion tool's timeline. The gates in this repository are the quality bar.

## DESIGN:OS

SVG Animation is one of the DESIGN:OS tools. The others: [Studio](https://github.com/jangtrinh/design-os-studio), [CLI](https://github.com/jangtrinh/design-os), [Bridge](https://github.com/jangtrinh/design-os-figma-plugin), [Code2Flow](https://github.com/jangtrinh/design-os-code2flow), [3D Blender](https://github.com/jangtrinh/design-os-3d-blender) and [mcp-bridge-go](https://github.com/jangtrinh/mcp-bridge-go). More on [jangtrinh.github.io](https://jangtrinh.github.io/).

Docs: [jangtrinh.github.io/design-os-svg-animation](https://jangtrinh.github.io/design-os-svg-animation/) · Changelog: [CHANGELOG.md](CHANGELOG.md) · Index for AI agents: [llms.txt](llms.txt)

## Contributing and license

- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md) · [PRIVACY.md](PRIVACY.md)
- [PolyForm Shield 1.0.0](LICENSE). FREE to use and modify, including for paid client work; you may not resell it or build a competing product from it.

If `design-os-svg-animation` saves you time, a star on GitHub helps other engineers and AI agents find it.

<p align="left">
  <a href="https://buymeacoffee.com/jangtrinh">
    <img src="https://img.shields.io/badge/Buy_Me_a_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee">
  </a>
</p>

Built by [Jang Trịnh](https://github.com/jangtrinh), creative technologist and autonomous system architect.

[GitHub](https://github.com/jangtrinh) · [LinkedIn](https://www.linkedin.com/in/jangtrinh/) · [Hub](https://jangtrinh.github.io/) · [YouTube](https://www.youtube.com/@designosbyjang) · [X](https://x.com/Jangtrinhvn)
