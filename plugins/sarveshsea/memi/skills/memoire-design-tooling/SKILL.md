---
name: memoire-design-tooling
description: Use when a task involves UI design, interface understanding, interface craft, Figma, design systems, shadcn/ui, Tailwind, UX audits, user research, Atomic Design, component specs, MCP, or design-to-code generation.
---

# memi Design Tooling

Use memi as the local interface-understanding layer before broad frontend changes. The goal is to give the agent evidence about the product UI before it edits code.

## Fast Path

```bash
npm i -g @memi-design/cli
memi suite init --project .
memi daemon start --project . --port auto
memi daemon status --json
memi agent install --dry-run --json
memi agent brief . --intent "Improve this interface" --json
memi status
memi diagnose .
memi ux audit . --json
memi craft audit . --json
memi tokens --from ./src --report
memi shadcn export --out public/r
memi mcp start --no-figma
```

## Interface Understanding Protocol

1. Read the local instructions first: `AGENTS.md`, README files, `.memoire/`, specs, tokens, and `memoire.agent.yaml`.
2. Generate a design-agent preflight with `memi agent brief . --intent "<task>" --json`; use it as the local evidence and cost-control contract.
3. Collect evidence with `memi diagnose .`, `memi ux audit . --json`, `memi craft audit . --json`, and `memi tokens --from ./src --report` before making broad UI edits.
4. If a runtime route matters, run `memi diagnose http://localhost:<port>` or `memi design-doc <url> --spec`.
5. If Figma is connected, use memi/Figma context for token pulls, component inspection, screenshot capture, and sync. Figma is optional; do not block code-first audits on it.
6. Map components to Atomic Design levels: atom, molecule, organism, template, page.
7. Prefer shadcn/ui primitives and Tailwind. Avoid introducing CSS modules or styled-components for memi-generated UI.
8. Use UX Tenets and Traps as the review layer: clarity, feedback, control, consistency, accessibility, error recovery, progressive disclosure, workflow fit, trust, and state continuity.
9. Use Interface Craft as the polish layer: focusing mechanism, visual hierarchy, spacing rhythm, color intentionality, visual weight, component cohesion, responsive resilience, and user context.
10. For research-backed product work, run the research flow before implementation:

```bash
memi research synthesize
memi simulate plan --hypothesis "Evidence links improve product confidence" --json
memi research design --intent "Design from the accepted research evidence" --json
memi research design --write-specs --mermaid-jam --json
memi mermaid-jam export --from research --json
```

11. For registry work, keep the output installable:

```bash
memi shadcn doctor
memi shadcn export --out public/r
memi publish --name @you/ds
memi add Button --from @you/ds
```

12. End with evidence: commands run, artifacts produced, files changed, remaining assumptions, and the next verification command.

## Agent Stack Setup

```bash
memi agent install universal --project .
memi agent install grok-build --project .
memi agent install hermes
memi agent install openclaw --project .
memi agent install claude-code --project .
memi agent install cursor --project .
memi agent install codex
memi agent install codex-plugin
memi agent install opencode --project .
npx skills add sarveshsea/memi --skill memoire-design-tooling
npx skills add emilkowalski/skills
```

Use `memi agent install --dry-run --json` before writing kit files in shared repositories.

**Dependency graph:** memi owns product-system evidence (tokens, audits, CI). For animation taste and design-engineering polish, depend on [emilkowalski/skills](https://github.com/emilkowalski/skills) rather than reinventing craft rules. Proof workspace: [sarveshsea/design-sandbox](https://github.com/sarveshsea/design-sandbox). Design CI Action: `uses: sarveshsea/memi@v2`.

## Review Format (UI diffs)

When reviewing UI against memi evidence, prefer a markdown table:

| Finding | Evidence | Fix |
| --- | --- | --- |
| Raw hex in Button | `memi tokens` / diagnose | Map to design token |
| Missing focus ring | `memi ux audit` | Restore focus styles |
| Hierarchy collapse | `memi craft audit` | One clear focal element |

## Output Artifacts To Cite

- `.memoire/app-quality/diagnosis.json`
- `.memoire/app-quality/diagnosis.md`
- `.memoire/app-quality/ux-audit.json`
- `.memoire/app-quality/interface-craft.json`
- `.memoire/design-system.json`
- `public/r/registry.json`
- `.memoire/mermaid-jam/<package-id>/`
- `memoire.agent.yaml`

## Common Mistakes

- Starting a UI patch before collecting design evidence.
- Treating Figma as mandatory when code-first audit commands are enough.
- Creating new component patterns when shadcn/ui or local components already exist.
- Omitting Atomic Design levels from new component specs.
- Ignoring UX trap findings because the screen looks acceptable in one viewport.
- Skipping interface craft checks, then relying on taste for hierarchy, rhythm, polish, or conventions.
- Installing agent kits without a dry run in a shared workspace.
- Skipping the design-agent brief, then guessing which evidence, agent stack, or cost mode applies.
- Reinventing animation craft rules instead of depending on proven upstream skills (e.g. `emilkowalski/skills`).
