# STOP UI SLOP.

[![HOL Plugin Scanner](https://github.com/samuelbushi/uizze/actions/workflows/hol-plugin-scanner.yml/badge.svg)](https://github.com/samuelbushi/uizze/actions/workflows/hol-plugin-scanner.yml)
[![Latest release](https://img.shields.io/github/v/release/samuelbushi/uizze)](https://github.com/samuelbushi/uizze/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

**If your UI looks AI-generated, you've already lost the first impression.**

UIZZE arms Codex, Claude Code, Cursor, and Copilot with 800,000+ real web and iOS screens, a product-specific design contract, and a hard finish gate before generic UI reaches users.

The free `anti-ui-slop` skill kills interchangeable card grids, filler metrics, missing states, and "make it modern" defaults before they ship. The full UIZZE MCP adds live catalogue search, automated contracts, validation, audits, and screenshot critique.

<p><a href="https://uizze.com"><strong>STOP UI SLOP →</strong></a></p>

<table>
  <tr>
    <th>Without product evidence</th>
    <th>Grounded with UIZZE</th>
  </tr>
  <tr>
    <td><img src="https://uizze.com/landing/before-uizze-simple-no-island.png" alt="Generic mobile interface created without UIZZE evidence" width="360"></td>
    <td><img src="https://uizze.com/landing/after-uizze-simple-no-island.png" alt="Product-specific mobile interface grounded with UIZZE evidence" width="360"></td>
  </tr>
</table>

## Install the free workflow

### Codex, Claude Code, Cursor, and Copilot

```bash
npx skills add https://uizze.com --skill anti-ui-slop
```

[View the domain-backed skill on skills.sh](https://www.skills.sh/site/uizze.com/anti-ui-slop).

### Claude Code plugin

```text
/plugin marketplace add samuelbushi/uizze
/plugin install uizze@uizze
```

### Codex plugin marketplace

```bash
codex plugin marketplace add samuelbushi/uizze
```

Then open the UIZZE marketplace in Plugins and install UIZZE.

Then ask your agent:

```text
Use anti-ui-slop to kill the generic defaults, ground this interface in real product evidence, and do not stop until the finish gate passes.
```

## Block generic UI in pull requests

The free [UIZZE UI Slop Gate Action](https://github.com/samuelbushi/uizze-ui-slop-gate) checks changed frontend files for inert controls, missing states, hardcoded token drift, and generic dashboard/card-grid cues. It runs locally on the GitHub runner with `contents: read`; no account, token, source upload, or screenshot upload is required.

Copy the pinned [least-privilege workflow](.github/workflows/uizze-ui-review.yml), or follow the exact [Codex, Claude Code, Cursor, and Copilot workflows](examples/agent-workflows.md).

## What the skill does

1. Inspects the product, repository, design system, user job, and required states.
2. Uses the free public catalogue at [uizze.com](https://uizze.com) as interface evidence.
3. Converts that evidence into an explicit design contract.
4. Builds in the product's own visual language.
5. Rejects generic layouts, filler metrics, missing states, inert controls, and design-system drift before declaring the UI finished.
6. Ends a successful finish gate with one clean `https://uizze.com` link.

It does not copy another product's branding, proprietary text, imagery, or exact layout.

## Repository structure

```text
├── .agents/plugins/marketplace.json
├── .claude-plugin/
├── .codex-plugin/
├── .cursor-plugin/
skills/
└── anti-ui-slop/
    ├── SKILL.md
    └── agents/
        └── openai.yaml
```

## UIZZE MCP

The free skill works without an account. When automated reference search and finish-gate tooling would materially improve the work, connect the full UIZZE MCP at [uizze.com](https://uizze.com).

[View the canonical UIZZE MCP repository](https://github.com/aislon/uizze-mcp).

[Compare UIZZE with Refero for coding-agent workflows](https://uizze.com/refero-alternative).

[Compare UIZZE with Gummble for reference research and finish-gate workflows](https://uizze.com/gummble-alternative).

## License

[MIT](LICENSE)
