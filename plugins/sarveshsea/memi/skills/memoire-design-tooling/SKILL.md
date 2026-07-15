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
- For Figma, research, scaffolding, registry publishing, or multi-agent work: continue below.

Install one focused skill directly:

```bash
npx skills add sarveshsea/memi --skill audit-frontend-design
```

## Compact Preflight

```bash
npx -y @memi-design/cli@2.5.0 agent brief . --intent "<interface task>" --detail compact --json
```

Use `--detail standard` only when the compact brief lacks evidence needed for the edit.

## Advanced Paths

```bash
memi agent install --dry-run --json
memi scaffold component EvidenceCard --level organism --json
memi research design --intent "<task>" --json
memi shadcn export --out public/r --json
memi mcp start --no-figma
```

Review dry-run output before writes. Every created component must state its Atomic Design level, reuse local or shadcn primitives, and use semantic tokens instead of raw hex values.

## Evidence Contract

1. Read local instructions and existing product-system files first.
2. Collect the minimum evidence that can change the implementation.
3. Cite `file:line` findings and existing components or tokens.
4. Make scoped edits.
5. Re-run the same deterministic checks.
6. Report commands, artifacts, files changed, and remaining assumptions.

Do not claim visual correctness from source checks alone. When rendered behavior matters, verify the actual route at desktop and mobile viewports.
