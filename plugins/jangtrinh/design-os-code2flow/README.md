# DESIGN:OS Code2Flow

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/readme/cover-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/readme/cover-light.png">
  <img src="docs/images/readme/cover-dark.png" alt="design:os by Jang" width="100%">
</picture>
</p>

A local CLI that turns a codebase into a user-flow map: screens, transitions, captured frames, and a lint on the graph. The command is `code2flow`. Package version 0.4.1, from `package.json`. Node 20 or later (`engines` in that file). The canvas is served on `http://127.0.0.1:4317` (`VIEWER_PORT` in `src/schema/stage-bridge-protocol.ts`).

Three adapters are registered in `src/parser/ingest.ts` today: Next.js App Router, React Router, and static HTML. Eight lint rules live in `src/lint/flow-lint.ts`: `orphan-screen`, `dead-end`, `not-captured`, `broken-link`, `low-confidence`, `needs-sample`, `login-gated`, and `capture-failed`. Twelve commands are dispatched in `src/cli/index.ts`.

FREE + source-available ([PolyForm Shield 1.0.0](LICENSE)). It runs locally, with no telemetry. See [PRIVACY.md](PRIVACY.md).

<p>
  <a href="#quickstart">Quickstart</a> · <a href="#what-it-makes">What it makes</a> · <a href="#how-it-works">How it works</a> · <a href="#commands">Commands</a> · <a href="#install-for-your-agent">Install</a> · <a href="#limits">Limits</a>
</p>

## Quickstart

**In Claude Code:**

```text
/plugin marketplace add jangtrinh/design-os-code2flow
/plugin install design-os-code2flow@design-os-code2flow
```

**From a clone:**

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git
cd design-os-code2flow
npm ci
npm run build
python3 scripts/self_check.py
```

Point the CLI at a repo it can actually read. After the build, the binary is `dist/cli/index.js` (the `code2flow` bin in `package.json`):

```bash
node dist/cli/index.js scan path/to/repo
node dist/cli/index.js lint path/to/repo
node dist/cli/index.js serve path/to/repo
```

`code2flow serve` opens the canvas on 127.0.0.1, port 4317.

## What it makes

These are real captures already in this repository, not mocks.

<p>
<img src="docs/assets/product-map.png" alt="design:os by Jang" width="100%">
</p>
<p>
<img src="docs/assets/feature-inspect.png" alt="design:os by Jang" width="100%">
</p>
<p>
<img src="docs/assets/stage-live.png" alt="design:os by Jang" width="100%">
</p>
<p>
<img src="docs/assets/terminal-run.gif" alt="design:os by Jang" width="100%">
</p>

A scan writes `.code2flow/graph.json`. `snapshot` captures each screen. `export` writes a self-contained HTML file. `render` writes PNG or PDF hand-outs. `lint` prints the eight rules above and can fail a CI job (`--fail-on`). `stories` scaffolds and validates a story manifest against the graph. `diff` compares two scans.

## How it works

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/readme/flow-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/readme/flow-light.png">
  <img src="docs/images/readme/flow-dark.png" alt="design:os by Jang" width="100%">
</picture>
</p>

`code2flow scan` picks an adapter from `src/parser/ingest.ts`, reads routes and transitions from the source, and writes the graph. `snapshot` and `run` capture frames when you give them a local URL. `lint` runs `lintFlow`. `serve` hosts the viewer on loopback. Nothing is uploaded.

TanStack Router, Expo Router, SwiftUI, Flutter and Jetpack Compose are not registered adapters in this version. Do not expect those codebases to scan until an adapter for them lands in `src/parser/ingest.ts`.

## Commands

From `src/cli/index.ts`:

| Command | What it does |
| :--- | :--- |
| `code2flow scan <repo>` | Parse routes, screens and transitions into `<repo>/.code2flow/graph.json` |
| `code2flow init <repo>` | Add local config and agent guidance (idempotent) |
| `code2flow run <repo>` | Scan, capture, validate, lint and export |
| `code2flow paths <repo> --from A --to B` | Shortest source-evidenced paths |
| `code2flow snapshot <repo> --url <devServer>` | Capture every screen |
| `code2flow login <repo> --url <devServer>` | Sign in once, reused by snapshot and run |
| `code2flow serve <repo>` | Open the canvas on http://127.0.0.1:4317 |
| `code2flow export <repo>` | Self-contained HTML |
| `code2flow render <repo>` | PNG or PDF hand-outs |
| `code2flow stories scaffold \| validate` | Story manifest from a PRD, then a check against the graph |
| `code2flow lint <repo>` | The eight rules in `src/lint/flow-lint.ts` |
| `code2flow diff <repo> --from <graph.json\|repo>` | What changed since an earlier scan |

`code2flow --help` prints the same list. `/doctor` and `python3 scripts/self_check.py` check the skill and the repo files.

## Install for your agent

Every option installs the same skill, `skills/design-os-code2flow/SKILL.md`.

**Claude Code:** the two `/plugin` commands in Quickstart.

**Codex**

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git /tmp/design-os-code2flow
mkdir -p ~/.codex/skills/design-os-code2flow ~/.codex/prompts
cp -R /tmp/design-os-code2flow/skills/design-os-code2flow/* ~/.codex/skills/design-os-code2flow/
cp /tmp/design-os-code2flow/prompts/doctor.md ~/.codex/prompts/design-os-code2flow-doctor.md
rm -rf /tmp/design-os-code2flow
```

**Gemini CLI and Antigravity**

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git /tmp/design-os-code2flow
mkdir -p ~/.gemini/skills/design-os-code2flow
cp -R /tmp/design-os-code2flow/skills/design-os-code2flow/* ~/.gemini/skills/design-os-code2flow/
rm -rf /tmp/design-os-code2flow
```

**OpenCode, Cursor, Windsurf and other harnesses**

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git /tmp/design-os-code2flow
mkdir -p ~/.agents/skills/design-os-code2flow
cp -R /tmp/design-os-code2flow/skills/design-os-code2flow/* ~/.agents/skills/design-os-code2flow/
rm -rf /tmp/design-os-code2flow
```


## Limits

Use this on a Next.js App Router, React Router, or static HTML repo. Other frameworks are not wired up yet. The lint is a static reading of the graph and of capture results; it is not a substitute for walking the product. Dynamic routes need concrete URLs in `code2flow.config.json` (`needs-sample`). Sign-in walls need `--storage-state` or `code2flow login`.

## DESIGN:OS

Code2Flow is one of the DESIGN:OS tools. The others: [Studio](https://github.com/jangtrinh/design-os-studio), [CLI](https://github.com/jangtrinh/design-os), [Bridge](https://github.com/jangtrinh/design-os-figma-plugin), [SVG Animation](https://github.com/jangtrinh/design-os-svg-animation), [3D Blender](https://github.com/jangtrinh/design-os-3d-blender) and [mcp-bridge-go](https://github.com/jangtrinh/mcp-bridge-go). More on [jangtrinh.github.io](https://jangtrinh.github.io/).

Docs: [jangtrinh.github.io/design-os-code2flow](https://jangtrinh.github.io/design-os-code2flow/) · Changelog: [CHANGELOG.md](CHANGELOG.md) · Index for AI agents: [llms.txt](llms.txt)

## Contributing and license

- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md) · [PRIVACY.md](PRIVACY.md)
- [PolyForm Shield 1.0.0](LICENSE). FREE to use and modify, including for paid client work; you may not resell it or build a competing product from it.

If `design-os-code2flow` saves you time, a star on GitHub helps other engineers and AI agents find it.

<p align="left">
  <a href="https://buymeacoffee.com/jangtrinh">
    <img src="https://img.shields.io/badge/Buy_Me_a_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee">
  </a>
</p>

Built by [Jang Trịnh](https://github.com/jangtrinh), creative technologist and autonomous system architect.

[GitHub](https://github.com/jangtrinh) · [LinkedIn](https://www.linkedin.com/in/jangtrinh/) · [Hub](https://jangtrinh.github.io/) · [YouTube](https://www.youtube.com/@designosbyjang) · [X](https://x.com/Jangtrinhvn)
