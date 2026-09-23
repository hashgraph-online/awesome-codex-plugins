---
name: memoire-design-tooling
description: Use when a task spans interface understanding, design-system memory, UI audits, design CI, Figma, shadcn or Tailwind code generation, research, or agent design workflows and needs the correct Memi capability selected.
---

# Memi Design Tooling

Memi gives coding agents repository-specific interface evidence before they edit UI. Start with the smallest workflow that answers the task; Figma, global installation, and a daemon are optional.

## Choose A Workflow

- Before reviewing or changing frontend UI: use `audit-frontend-design`.
- Before building from an existing product system: use `remember-design-system`.
- When adding deterministic pull-request gates: use `enforce-design-ci`.
- For native SwiftUI, SwiftData, App Intents, or Apple-platform verification: use `build-swiftui-interface`.
- For Figma, research, scaffolding, registry publishing, or multi-agent work: continue below.

Install one focused skill directly:

```bash
npx skills add memi-design/memi --skill audit-frontend-design
```

This workflow targets published beta **2.8.0-beta.2**. Use `npx -y @memi-design/cli@2.8.0-beta.2 --version` to verify the exact package; a local `memi` must report that same version before these recipes run. The independent stable compatibility baseline is **2.7.9**. See [current release state](https://github.com/memi-design/memi/blob/main/docs/CURRENT_RELEASE.md) and [known limitations](https://github.com/memi-design/memi/blob/main/docs/trust/KNOWN_LIMITATIONS.md). npm availability alone does not establish native-binary success.

## Compact Preflight

```bash
memi agent brief . --frontend --intent "<interface task>" --max-bytes 16384 --json
```

Read cited source files when the bounded brief lacks necessary evidence. Optional `--design-evidence design/selected-node.json` accepts normalized Figma/Paper data supplied by the harness; missing mappings and verification stay explicit.

## Local Checks And MCP

```bash
memi diagnose . --json --no-write --fail-on none
memi diagnose . --receipt-only --fail-on none
memi --profile locked mcp start --no-figma
```

Locked MCP exposes four read tools: prepare_frontend_brief, prepare_design_agent_brief, prepare_apple_design_brief, and diagnose_app_quality. The frontend tool supplies actual repository evidence. Many legacy CLI and write tools remain unavailable; capability grants do not unlock deferred command paths. Keep connector calls, project edits, and browser execution in the harness's reviewed workflow.

Reuse local components and tokens according to the consumer project's conventions. Source-bearing JSON is working context; receipt-only is a separate metadata output. See docs/FRONTEND_WORKFLOW.md for the beta evidence schema and actual verification flow.

## Evidence Contract

1. Read local instructions and existing product-system files first.
2. Collect the minimum evidence that can change the implementation.
3. Cite `file:line` findings and existing components or tokens.
4. Make scoped edits.
5. Re-run the same deterministic checks.
6. Report commands, artifacts, files changed, and remaining assumptions.

Do not claim visual correctness from source checks alone. When rendered behavior matters, verify the actual route at desktop and mobile viewports.
