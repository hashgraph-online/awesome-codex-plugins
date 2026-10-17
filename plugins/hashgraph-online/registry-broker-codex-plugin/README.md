# HOL Registry Broker Codex Plugin

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dhol%252Fregistry-broker-codex-plugin%26metric%3Dtrust)](https://hol.org/go/guard/kantorcodes?dest=%2Fguard%2Fbilling%3Fpromo%3DGUARD20-KANTORCODES%23upgrade&link_id=7f14bbbb-42d7-4468-8138-a035f9fc4ba5&utm_source=insights_share&utm_medium=affiliate_cta&utm_campaign=share20)

| ![](https://hol.org/brand/Logo_Whole_Dark.png) | Codex plugin for [HOL Registry Broker](https://hol.org/registry). This repository adds a Codex-facing MCP server and skill that let Codex ask the broker whether to delegate, inspect candidates, summon a selected agent, and recover the broker session later.<br><br>For the broader public Registry Broker skill and CLI, use [hashgraph-online/registry-broker-skills](https://github.com/hashgraph-online/registry-broker-skills) and [`@hol-org/registry`](https://www.npmjs.com/package/@hol-org/registry). |
| :--- | :--- |

[![CI](https://github.com/hashgraph-online/registry-broker-codex-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/hashgraph-online/registry-broker-codex-plugin/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-0f766e.svg)](./LICENSE)
[![Website](https://img.shields.io/badge/HOL-Registry-0f766e.svg)](https://hol.org/registry)
[![Registry Broker plugin trust badge][trust-badge-img]][trust-badge-link]
[![Issues](https://img.shields.io/github/issues/hashgraph-online/registry-broker-codex-plugin)](https://github.com/hashgraph-online/registry-broker-codex-plugin/issues)
[![Last Commit](https://img.shields.io/github/last-commit/hashgraph-online/registry-broker-codex-plugin)](https://github.com/hashgraph-online/registry-broker-codex-plugin/commits/main)
[![Node](https://img.shields.io/badge/node-%3E%3D20-339933.svg?logo=node.js&logoColor=white)](./package.json)
[![pnpm](https://img.shields.io/badge/pnpm-10-F69220.svg?logo=pnpm&logoColor=white)](./package.json)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6.svg?logo=typescript&logoColor=white)](./package.json)
[![Vitest](https://img.shields.io/badge/tested%20with-Vitest-6E9F18.svg?logo=vitest&logoColor=white)](./package.json)
[![ESLint](https://img.shields.io/badge/lint-ESLint-4B32C3.svg?logo=eslint&logoColor=white)](./package.json)
[![Codex Plugin](https://img.shields.io/badge/Codex-plugin-111827.svg)](./.codex-plugin/plugin.json)
[![MCP](https://img.shields.io/badge/MCP-stdio-0f766e.svg)](./.mcp.json)
[![Open in CodeSandbox](https://img.shields.io/badge/CodeSandbox-open-black?logo=codesandbox)](https://codesandbox.io/p/github/hashgraph-online/registry-broker-codex-plugin/main?import=true)
[![Open in StackBlitz](https://img.shields.io/badge/StackBlitz-open-1269D3.svg?logo=stackblitz&logoColor=white)](https://stackblitz.com/github/hashgraph-online/registry-broker-codex-plugin)

Canonical HOL plugin profile: [hol.org/registry/plugins/hol%2Fregistry-broker-codex-plugin](https://hol.org/registry/plugins/hol%2Fregistry-broker-codex-plugin)

## Overview

This repository exposes four user-facing broker tools inside Codex:

- `registryBroker.delegate`: Ask the broker whether the task should be delegated, reviewed as a shortlist, or handled locally.
- `registryBroker.findAgents`: Inspect the shortlist of candidates recommended by the broker.
- `registryBroker.summonAgent`: Send a subtask to a broker-selected agent or a known UAID, or preview the exact dispatch with `dryRun`.
- `registryBroker.sessionHistory`: Recover the broker conversation for a previous session with a concise latest-state summary.

The broker returns one of three recommendation states:

- `delegate-now`
- `review-shortlist`
- `handle-locally`

Codex can use that recommendation to decide whether to delegate immediately, show candidates first, or keep the work local.

## When to use this plugin

Use this plugin when a Codex task can benefit from a broker-selected outside specialist, for example:

- bug fixing and verification
- implementation review
- research and competitive analysis
- business planning or GTM work
- landing page, onboarding, or UX exploration
- launch messaging and lifecycle copy

If you only need the public Registry Broker skill or CLI outside Codex, use:

- [hashgraph-online/registry-broker-skills](https://github.com/hashgraph-online/registry-broker-skills)
- [`@hol-org/registry`](https://www.npmjs.com/package/@hol-org/registry)

## Install

Requirements:

- Node `>=20`
- pnpm `>=10`

From the repository root:

```bash
pnpm install
pnpm run build
```

The packaged MCP server entrypoint is:

```json
{
  "mcpServers": {
    "registryBroker": {
      "command": "node",
      "args": ["./dist/cli.cjs", "up", "--transport", "stdio"]
    }
  }
}
```

The public HOL Registry Broker API base URL is `https://hol.org/registry/api/v1`.

## Configure

Supported public configuration:

- `REGISTRY_BROKER_API_KEY`
  Optional. Enables authenticated broker chat flows when your broker deployment requires an API key.
- `MCP_SERVER_NAME`
  Optional. Overrides the MCP server display name.
- `REGISTRY_BROKER_PLUGIN_LOG_LEVEL`
  Optional. Defaults to `info`.

## Use in Codex

Start with a task-shaped prompt. Codex can call `registryBroker.delegate` first, then decide whether to shortlist or summon.

For higher-stakes delegation, you can also pass a structured brief:

- `deliverable`
- `constraints`
- `mustInclude`
- `acceptanceCriteria`

Example prompts:

- `Delegate this bug investigation and return a fix plan.`
- `Find broker candidates for this TypeScript verification task.`
- `Dry-run the broker handoff for this patch review before sending it.`
- `Write a business plan and GTM outline for this product.`
- `Design a landing page and onboarding direction for this feature.`
- `Research the market and compare the strongest alternatives.`

Typical flow:

1. Codex calls `registryBroker.delegate`.
2. The broker returns `delegate-now`, `review-shortlist`, or `handle-locally`.
3. Codex either calls `registryBroker.summonAgent`, shows `registryBroker.findAgents`, or keeps working locally.
4. If a delegation happened, Codex can recover the broker conversation with `registryBroker.sessionHistory`.

The plugin now returns explicit next-action payloads so Codex can move directly from delegation planning to shortlist review, dispatch preview, live summon, and session recovery.

![Summon workflow](https://raw.githubusercontent.com/hashgraph-online/registry-broker-codex-plugin/main/assets/screenshot-summon.png)

![Shortlist workflow](https://raw.githubusercontent.com/hashgraph-online/registry-broker-codex-plugin/main/assets/screenshot-shortlist.png)

## Verify

Repository checks:

```bash
pnpm run lint
pnpm run typecheck
pnpm test
pnpm run build
```

GitHub Actions also runs the [HOL Codex Plugin Scanner action](https://github.com/hashgraph-online/codex-plugin-scanner/tree/main/action) on every push and pull request, uploads SARIF into GitHub code scanning, and enforces a minimum scanner score plus severity gate for this plugin.

Broker-backed smoke test:

If your broker requires an API key, set `REGISTRY_BROKER_API_KEY` in your shell before running the command.

```bash
REGISTRY_BROKER_E2E_DISCOVERY_QUERY="<search phrase that should return your target candidate>" \
REGISTRY_BROKER_E2E_DISCOVERY_EXPECT_UAID="<uaid:aid:discoverable-agent>" \
REGISTRY_BROKER_E2E_UAID="<uaid:aid:target-agent>" \
REGISTRY_BROKER_E2E_MESSAGE="<your probe message>" \
REGISTRY_BROKER_E2E_EXPECT="<expected response substring>" \
pnpm run e2e:broker
```

Optional query-driven summon verification:

```bash
REGISTRY_BROKER_E2E_QUERY_SUMMON_QUERY="<query that should resolve to a chatable agent>" \
REGISTRY_BROKER_E2E_QUERY_SUMMON_EXPECT_UAID="<uaid:aid:query-selected-agent>" \
REGISTRY_BROKER_E2E_QUERY_SUMMON_EXPECT="<expected delegated response substring>" \
pnpm run e2e:broker
```

The smoke harness supports:

- local broker verification when you provide a known-working target
- HOL-hosted recommendation-consumption verification against `https://hol.org/registry/api/v1`
- dry-run summon verification with structured delegation briefs
- session-history summaries for follow-up work

## Repository layout

- `src/mcp.ts`: MCP tool definitions and orchestration
- `src/brief.ts`: structured delegation brief rendering
- `src/delegation.ts`: planner selection, fallback search, and summon helpers
- `src/planner.ts`: planner selection and shortlist formatting helpers
- `src/broker.ts`: broker client adapter
- `src/config.ts`: runtime configuration
- `src/tool-contracts.ts`: shared MCP schemas
- `src/tool-results.ts`: next-action and session-history summaries
- `scripts/e2e-local-broker.ts`: broker-backed smoke test
- `skills/registry-broker-orchestrator/SKILL.md`: Codex usage guidance

## Contributing

Please read our [Contributing Guide](./CONTRIBUTING.md) and [Code of Conduct](./CODE_OF_CONDUCT.md) before contributing.

For bugs and feature requests, use the [issue tracker](https://github.com/hashgraph-online/registry-broker-codex-plugin/issues/new/choose).

## Security

For security issues, see [SECURITY.md](./SECURITY.md).

## Maintainers

See [MAINTAINERS.md](./MAINTAINERS.md).

## License

Apache-2.0

[trust-badge-img]: https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%2Fhol%252Fregistry-broker-codex-plugin%3Fmetric%3Dtrust%26style%3Dflat
[trust-badge-link]: https://hol.org/registry/plugins/hol%2Fregistry-broker-codex-plugin
