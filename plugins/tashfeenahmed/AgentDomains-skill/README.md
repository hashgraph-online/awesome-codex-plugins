<div align="center">

# agent·domains skill

### Teach your AI agent to claim its own free public domain.



[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-2D6BFF)](https://docs.anthropic.com/en/docs/claude-code)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skills-compatible-2D6BFF)](https://www.anthropic.com)
[![skills.sh](https://img.shields.io/badge/skills.sh-npx%20skills%20add-141210)](https://skills.sh)
[![License: FSL-1.1](https://img.shields.io/badge/license-FSL--1.1--Apache--2.0-2D6BFF)](./LICENSE)

[**Website**](https://agentdomains.co) · [**Docs**](https://docs.agentdomains.co) · [**CLI**](https://github.com/tashfeenahmed/AgentDomains)

</div>

<p align="center">
  <img src="docs/skill-flow.svg" alt="AgentDomains skill flow: install → agent decides → claim → live" width="100%">
</p>

A Claude / agent **skill** for [AgentDomains](https://agentdomains.co): claim and manage
free domains (`makes.fyi` or `agentdomains.co`) for the sites an AI agent builds,
straight from the agent. Signup needs nothing; the first name needs an email address.

## What it does

Teaches an agent to get a real public hostname (`yourname.makes.fyi` or
`yourname.agentdomains.co`) on demand, to expose a server, set up a webhook, host a
site, or give itself a stable address, using the [`agentdomains`](https://github.com/tashfeenahmed/AgentDomains)
CLI. The skill loads only when it fits the task, then drives signup and `claim` for the agent.

It also covers the undo half, which is where an agent left to guess does the most
damage: removing a single DNS record rather than the whole name, knowing that a
forward or a proxy replaces the address records on a name, and closing the account
when it is genuinely finished with.

> **Prefer MCP?** There is also an MCP server —
> [`agentdomains-mcp`](https://github.com/tashfeenahmed/AgentDomains-mcp) — exposing the same
> operations as seventeen typed tools. Two ways to run it: the hosted endpoint at
> **`https://mcp.agentdomains.co`** (Streamable HTTP, nothing to install), or the npm package
> **`agentdomains-mcp`** locally over stdio (`npx -y agentdomains-mcp`). The **same `adom_…` API
> key** works for the skill's CLI, the MCP server, and the HTTP API — nothing separate to
> provision. This skill and the MCP server are independent; use whichever suits your setup.
> See the [MCP docs](https://docs.agentdomains.co/#mcp).

> **Cost:** free for up to ten names per account, with no card. An optional Pro plan
> ($5/month) holds 100 names; the skill tells the agent to offer it only when the user
> hits the limit, and never to pay. See [pricing](https://agentdomains.co/pricing).

## Install

### Codex / ChatGPT (plugin marketplace)

This repo doubles as a Codex repo marketplace (`.agents/plugins/marketplace.json`), so
Codex can add it directly:

```bash
codex plugin marketplace add tashfeenahmed/AgentDomains-skill
```

Then install `agentdomains` from the marketplace in the Codex app or CLI. The plugin
ships the same `SKILL.md` as the Claude Code plugin.

### Claude Code (plugin marketplace)

```text
/plugin marketplace add tashfeenahmed/AgentDomains-skill
/plugin install agentdomains@agentdomains
```

### Vercel skills.sh (Claude Code, Codex, Cursor, OpenClaw)

```bash
npx skills add tashfeenahmed/AgentDomains-skill
```

### ClawHub (OpenClaw)

```bash
openclaw skills install @tashfeenahmed/agentdomains
```

Or, without OpenClaw, straight from the registry with the ClawHub CLI:

```bash
npx clawhub install tashfeenahmed/agentdomains
```

The listing lives at
[clawhub.ai/tashfeenahmed/skills/agentdomains](https://clawhub.ai/tashfeenahmed/skills/agentdomains).

### Manual (any Agent Skills–compatible tool)

```bash
git clone https://github.com/tashfeenahmed/AgentDomains-skill
cp -r AgentDomains-skill/plugins/agentdomains/skills/agentdomains ~/.claude/skills/
```

The skill itself lives at
[`plugins/agentdomains/skills/agentdomains/SKILL.md`](plugins/agentdomains/skills/agentdomains/SKILL.md)
and follows the open [Agent Skills](https://www.anthropic.com) specification, so it also
works with Codex CLI and ChatGPT.

## Repository layout

```text
.claude-plugin/marketplace.json        # Claude Code marketplace manifest (this repo is a marketplace)
.agents/plugins/marketplace.json       # Codex / ChatGPT marketplace manifest (same repo, second client)
plugins/agentdomains/
  .claude-plugin/plugin.json           # Claude Code plugin manifest
  .codex-plugin/plugin.json            # Codex / ChatGPT plugin manifest
  skills/agentdomains/
    SKILL.md                           # the skill (name + description frontmatter)
    scripts/setup.sh                   # installs the CLI + creates an account
```

## Discoverability

This repo is structured as a Claude Code plugin marketplace, so it can be auto-indexed by
directories like [claudemarketplaces.com](https://claudemarketplaces.com),
[SkillsMP](https://skillsmp.com), and [LobeHub](https://lobehub.com/skills). The Codex
marketplace manifest under `.agents/plugins/` makes the same plugin readable by
Codex-compatible directories, e.g.
[awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins).

The skill is also published to [ClawHub](https://clawhub.ai/tashfeenahmed/skills/agentdomains),
the OpenClaw registry, where it is installable by handle. That one is *not* auto-indexed: a new
version has to be pushed by hand, so a release here does not reach ClawHub on its own. The steps
are in [`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## License

[FSL-1.1-Apache-2.0](./LICENSE).
