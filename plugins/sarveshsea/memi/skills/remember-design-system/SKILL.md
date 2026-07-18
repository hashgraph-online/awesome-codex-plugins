---
name: remember-design-system
description: Use when an agent is about to build or refactor interface code and needs a compact, repository-specific brief covering existing tokens, components, routes, conventions, and verification commands.
---

# Remember The Design System

Build design context from the repository instead of guessing from the prompt. This is a preflight for UI work, not a request to redesign the product.

## Build The Brief

Translate the user's task into a short intent, then run from the repository root:

```bash
npx -y @memi-design/cli@2.6.2 agent brief . --intent "<user's interface task>" --detail compact --json
```

If the task changes colors, spacing, typography, radii, or shadows, add token evidence:

```bash
npx -y @memi-design/cli@2.6.2 tokens --from ./src --report --json
```

## Apply The Memory

1. Prefer existing components and shadcn primitives over new abstractions.
2. Map every new component to atom, molecule, organism, template, or page.
3. Reuse semantic CSS variables and Tailwind theme tokens. Do not introduce raw hex values when a token exists.
4. Preserve route, state, loading, empty, error, focus, and responsive behavior identified by the brief.
5. Expand to `--detail standard` only when compact output omits evidence needed for the edit.

## Handoff

Before editing, state the components and tokens you will reuse. After editing, cite files changed, evidence followed, checks run, and any design assumptions that remain.
