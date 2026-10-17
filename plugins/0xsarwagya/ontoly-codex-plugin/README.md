# Ontoly Codex Plugin

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fguard%2Fhashgraph-online%2Fhol-guard-plugin)](https://hol.org/go/guard/sarwagyasingh69?dest=%2Fguard%2Fbilling%3Fpromo%3DGUARD20-SARWAGYASINGH69%23upgrade&link_id=8aab4f0e-d950-4ba5-89f1-5689b7c867c8&utm_source=insights_share&utm_medium=affiliate_cta&utm_campaign=share20)
[![HOL Plugin Scanner](https://github.com/0xsarwagya/ontoly-codex-plugin/actions/workflows/hol-plugin-scanner.yml/badge.svg)](https://github.com/0xsarwagya/ontoly-codex-plugin/actions/workflows/hol-plugin-scanner.yml)
[![npm install](https://img.shields.io/badge/npm-install-CB3837?logo=npm&logoColor=white)](#install-official-ontoly-skills)
[![License](https://img.shields.io/github/license/0xsarwagya/ontoly-codex-plugin)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-ready-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

Ontoly is a TypeScript-native software intelligence engine that builds a deterministic Software Graph.

This Codex plugin teaches agents to use Ontoly graph evidence, CLI reports, MCP, and the official Ontoly Agent Skills before falling back to broad repository search.

## What Is Included

- `.codex-plugin/plugin.json` declares the Codex plugin metadata.
- `skills/ontoly-software-graph/` teaches the graph-first workflow for architecture review, dependency analysis, impact analysis, request tracing, configuration analysis, security review, and codebase onboarding.
- The full Ontoly source and official task-specific skills live in [`0xsarwagya/ontoly`](https://github.com/0xsarwagya/ontoly).

## Install Official Ontoly Skills

```bash
npx skills add 0xsarwagya/ontoly --list
npx skills add 0xsarwagya/ontoly --skill architecture-review
npx skills add 0xsarwagya/ontoly --skill impact-analysis
npx skills add 0xsarwagya/ontoly --skill request-tracing
```

## Use Ontoly In A Repository

```bash
pnpm add -D @0xsarwagya/ontoly-cli
pnpm ontoly build .
pnpm ontoly stats .
pnpm ontoly mcp
```

## Validation

```bash
python3 /Users/shrey/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 /Users/shrey/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ontoly-software-graph
plugin-scanner scan . --format text
```
