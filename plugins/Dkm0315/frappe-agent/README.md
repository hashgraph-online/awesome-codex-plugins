# Frappe Agent for Codex

[![HOL Trust Score](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Ddhairya-marwaha%252Ffrappe-agent%26metric%3Dtrust%26style%3Dflat)](https://hol.org/registry/plugins/dhairya-marwaha%2Ffrappe-agent)
[![HOL Security](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Ddhairya-marwaha%252Ffrappe-agent%26metric%3Dsecurity%26style%3Dflat)](https://hol.org/registry/plugins/dhairya-marwaha%2Ffrappe-agent)
[![Release](https://img.shields.io/github/v/release/Dkm0315/frappe-agent)](https://github.com/Dkm0315/frappe-agent/releases)
[![License](https://img.shields.io/github/license/Dkm0315/frappe-agent)](./LICENSE)

`frappe-agent` is a Codex plugin for Frappe Framework and ERPNext development. It makes Codex more aware of Frappe-specific patterns so it can inspect benches more safely, choose the right customization layer, and avoid generic framework mistakes.

## What It Covers

- Frappe full-stack reasoning across backend, frontend, customization, and bench work
- Bench-aware inspection before app installs, migrations, or environment changes
- Frappe-native SQL and ORM guidance
- Customization-layer routing for `Custom Field`, `Property Setter`, `Client Script`, `Server Script`, `Workspace`, `Web Page`, `Report`, `Dashboard`, and related surfaces
- DocType form UX guidance for useful fields, tabs, sections, columns, and required-field discipline
- ERPNext-aware guidance for deciding between configuration, metadata, workflow, and code changes
- Frontend guidance for Vue, React, `frappe-ui`, desk pages, `www`, and external SPA patterns

## Included Skills

- `frappe-fullstack`
- `frappe-backend`
- `frappe-frontend`
- `frappe-bench`
- `frappe-sql`
- `frappe-customization`
- `frappe-doctype-design`
- `frappe-search`
- `frappe-erpnext`

## Installation

This repository currently ships:

- a real Codex plugin
- a native Claude Code plugin package and marketplace file
- portable and reusable Cursor rules plus command files
- GitHub Copilot repository instructions

### Codex

Codex supports repo marketplaces and local plugin installation.

If you cloned this repository locally, add it as a local marketplace:

```bash
codex marketplace add /path/to/frappe-agent
```

Then enable `frappe-agent` from the added marketplace in Codex and restart Codex in a fresh session.

Local repo flow:

1. Clone this repository somewhere on disk.
2. Run:

```bash
codex marketplace add /path/to/frappe-agent
```

3. Enable `frappe-agent` from that marketplace in Codex.
4. Restart Codex.

GitHub repo flow:

1. Clone this repository or open the repo locally.
2. Run:

```bash
codex marketplace add /path/to/local/clone/of/frappe-agent
```

3. Enable `frappe-agent` and restart Codex.

This repo includes:

- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

so it can act as a self-contained Codex plugin repository.

### Claude Code

Claude Code supports plugins and plugin marketplaces.

This repository now includes:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `commands/`
- `skills/`

Install from GitHub with:

```text
/plugin marketplace add Dkm0315/frappe-agent
/plugin install frappe-agent@frappe-agent --scope local
```

Install from a local clone with:

```text
/plugin marketplace add /path/to/frappe-agent
/plugin install frappe-agent@frappe-agent --scope local
```

For local development:

```bash
claude --plugin-dir /path/to/frappe-agent
```

Local repo flow:

1. Clone this repository locally.
2. In Claude Code, run:

```text
/plugin marketplace add /path/to/frappe-agent
/plugin install frappe-agent@frappe-agent --scope local
```

3. Run `/reload-plugins` if Claude is already open.

After updates during a session, reload plugins with:

```text
/reload-plugins
```

### Cursor

Cursor uses repository instructions such as `AGENTS.md`, `.cursor/rules`, and `.cursor/commands`.

This repository now includes:

- `AGENTS.md`
- `.cursor/rules/frappe-agent.mdc`
- `.cursor/commands/*.md`

To install them into a local project repository:

```bash
cp /path/to/frappe-agent/AGENTS.md /path/to/your-frappe-project/AGENTS.md
mkdir -p /path/to/your-frappe-project/.cursor/rules
cp /path/to/frappe-agent/.cursor/rules/frappe-agent.mdc /path/to/your-frappe-project/.cursor/rules/frappe-agent.mdc
mkdir -p /path/to/your-frappe-project/.cursor/commands
cp /path/to/frappe-agent/.cursor/commands/*.md /path/to/your-frappe-project/.cursor/commands/
```

Or use symlinks during development:

```bash
ln -s /path/to/frappe-agent/AGENTS.md /path/to/your-frappe-project/AGENTS.md
mkdir -p /path/to/your-frappe-project/.cursor
ln -s /path/to/frappe-agent/.cursor/rules /path/to/your-frappe-project/.cursor/rules
ln -s /path/to/frappe-agent/.cursor/commands /path/to/your-frappe-project/.cursor/commands
```

Cursor does not currently use the same repo-marketplace plugin install flow here that Claude Code does, so the practical local installation path is still repo-level rules and commands.

### GitHub Copilot

Copilot uses repository custom instructions and agent instructions.

To install the local guidance into a repository:

```bash
mkdir -p /path/to/your-frappe-project/.github
cp /path/to/frappe-agent/.github/copilot-instructions.md /path/to/your-frappe-project/.github/copilot-instructions.md
cp /path/to/frappe-agent/AGENTS.md /path/to/your-frappe-project/AGENTS.md
```

Or use symlinks during development:

```bash
mkdir -p /path/to/your-frappe-project/.github
ln -s /path/to/frappe-agent/.github/copilot-instructions.md /path/to/your-frappe-project/.github/copilot-instructions.md
ln -s /path/to/frappe-agent/AGENTS.md /path/to/your-frappe-project/AGENTS.md
```

Copilot does not use the same plugin marketplace flow here, so the practical local installation path is repository instructions.

## Releases

GitHub Releases are built by `.github/workflows/release.yml`.

Create a release from a tag:

```bash
git tag v0.1.0
git push upstream v0.1.0
```

Or run the `Release` workflow manually from GitHub Actions and provide a version such as `0.1.0`.

Each release uploads:

- `frappe-agent-{version}.zip`
- `frappe-agent-{version}.tar.gz`
- `frappe-agent-{version}.sha256`

## Usage Examples

Ask Codex to use the plugin naturally in the prompt:

```text
Use Frappe Agent to inspect this bench before changing anything.
```

```text
Use Frappe Agent to choose the right Frappe customization layer for adding fields to Sales Order.
```

```text
Use Frappe Agent to design a clean DocType layout for a service request workflow.
```

```text
Use Frappe Agent to review whether this Frappe SQL should use frappe.db, frappe.qb, or raw SQL.
```

```text
Use Frappe Agent to decide whether this UI should be a desk page, a www page, a Vue frappe-ui page, or a React SPA.
```

## Repository Layout

```text
frappe-agent/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .cursor/
│   ├── commands/
│   │   ├── frappe-backend.md
│   │   ├── frappe-bench.md
│   │   ├── frappe-customization.md
│   │   ├── frappe-doctype-design.md
│   │   ├── frappe-erpnext.md
│   │   ├── frappe-frontend.md
│   │   ├── frappe-fullstack.md
│   │   ├── frappe-search.md
│   │   └── frappe-sql.md
│   └── rules/
│       └── frappe-agent.mdc
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/
│       └── release.yml
├── AGENTS.md
├── CLAUDE.md
├── commands/
│   ├── frappe-backend.md
│   ├── frappe-bench.md
│   ├── frappe-customization.md
│   ├── frappe-doctype-design.md
│   ├── frappe-erpnext.md
│   ├── frappe-frontend.md
│   ├── frappe-fullstack.md
│   ├── frappe-search.md
│   └── frappe-sql.md
├── skills/
│   ├── frappe-backend/
│   ├── frappe-bench/
│   ├── frappe-customization/
│   ├── frappe-doctype-design/
│   ├── frappe-erpnext/
│   ├── frappe-frontend/
│   ├── frappe-fullstack/
│   ├── frappe-search/
│   └── frappe-sql/
└── README.md
```

## Current Scope

This repository is now:

- a Codex-native plugin package
- a Claude Code-native plugin package
- a Cursor-ready repository rules and commands bundle
- a Copilot-ready repository instructions bundle

Planned future work:

- official Claude marketplace submission
- richer Cursor command bundles
- deeper Copilot instruction coverage

## Design Goals

- Inspect first, mutate second
- Prefer Frappe-native customization surfaces before invasive code changes
- Separate ERPNext configuration work from framework-code work
- Respect bench context, app provenance, and version boundaries
- Help agents make fewer generic Python, JavaScript, SQL, and frontend mistakes in Frappe codebases

## Roadmap

- Add more first-class skills for custom fields, reports, workflows, dashboards, and upgrade planning
- Add better source-backed command and flag coverage for Bench
- Add distribution adapters for Claude Code, Cursor, and Copilot
- Add richer repo examples and team onboarding docs

## License

MIT
