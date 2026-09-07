> **Stop AI coding agents from shipping generic UI.**

# Stop Making UI Slop

Build product-specific UI with free skills and, when useful, focused
references from [UIZZE](https://uizze.com).

![Stop Making UI Slop with UIZZE](https://uizze.com/landing/anti-ui-slop-skill-banner.png)

[![CI](https://github.com/uizze/uizze/actions/workflows/ci.yml/badge.svg)](https://github.com/uizze/uizze/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

## Install a skill

Use `ui-design` as the broad design and implementation workflow:

```bash
npx skills add https://uizze.com --skill ui-design
```

Use `anti-ui-slop` when the task is specifically about preventing or reviewing
generic UI:

```bash
npx skills add https://uizze.com --skill anti-ui-slop
```

The skills work without an account, token, script, or MCP connection. The
domain packages are canonical; this repository mirrors them for GitHub-native
installers.

## Connect the paid MCP

Create an agent token in [UIZZE](https://uizze.com), keep it out of source
control, and connect the authenticated endpoint:

```bash
export UIZZE_AGENT_TOKEN="uizze_at_your_token"
codex mcp add uizze --url https://uizze.com/mcp --bearer-token-env-var UIZZE_AGENT_TOKEN
```

The MCP intentionally exposes two tools:

- `find_ui_references` — find or inspect up to three full-screen references.
- `find_ui_materials` — find up to three hosted fonts, icons, animated icons,
  or explicitly requested packs.

No result is a valid result. Agents should continue with the product's existing
system instead of retrying or inventing advice.

## GitHub Action

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v4
  - uses: uizze/uizze@v1
```

The action performs a conservative source check on the GitHub runner. It does
not upload source or replace visual, accessibility, security, or usability
review. See [integrations/github-action](integrations/github-action).

## Repository map

| Path | Purpose |
| --- | --- |
| [`skills/anti-ui-slop`](skills/anti-ui-slop) | Prevent or review generic UI |
| [`skills/ui-design`](skills/ui-design) | Design, build, redesign, or improve interfaces |
| [`skills/ui-radar`](skills/ui-radar) | Find and compare focused UI references |
| [`integrations/mcp`](integrations/mcp) | Authenticated MCP setup and registry metadata |
| [`integrations/github-action`](integrations/github-action) | Local pull-request source check |
| [`integrations`](integrations) | Optional examples and host-specific packaging |

Production metadata is authoritative:

- [Agent Skills index](https://uizze.com/.well-known/agent-skills/index.json)
- [MCP manifest](https://uizze.com/.well-known/mcp.json)
- [MCP server card](https://uizze.com/.well-known/mcp/server-card.json)
- [Setup documentation](https://uizze.com/docs)

Public directory status lives in [DISTRIBUTION.md](DISTRIBUTION.md). It is a
short inventory, not a submission backlog.

## License

[MIT](LICENSE). Bundled third-party material retains its own notices and license.
