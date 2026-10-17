---
name: remember-design-system
description: Use when an agent is about to build or refactor interface code and needs a compact, repository-specific brief covering existing tokens, components, routes, conventions, and verification commands.
---

# Remember The Design System

Build design context from the repository instead of guessing from the prompt. This is a preflight for UI work, not a request to redesign the product.

This workflow targets published beta **2.8.0-beta.2**. Use `npx -y @memi-design/cli@2.8.0-beta.2 --version` to verify the exact package; a local `memi` must report that same version before these recipes run. The independent stable compatibility baseline is **2.7.9**. See [current release state](https://github.com/memi-design/memi/blob/main/docs/CURRENT_RELEASE.md) and [known limitations](https://github.com/memi-design/memi/blob/main/docs/trust/KNOWN_LIMITATIONS.md). npm availability alone does not establish native-binary success.

## Build The Brief

Translate the user's task into a short intent, then run from the repository root:

```bash
memi agent brief . --frontend --intent "<user's interface task>" --max-bytes 16384 --json
```

The frontend brief already includes bounded token and story evidence. For a selected Figma or Paper node, use the harness connector and supply its normalized evidence:

```bash
memi agent brief . --frontend --intent "<task>" --design-evidence design/selected-node.json --json
```

## Apply The Memory

1. Prefer existing components and the project's conventions. Do not impose a new component library or CSS framework.
2. Map every new component to atom, molecule, organism, template, or page.
3. Reuse semantic CSS variables and Tailwind theme tokens. Do not introduce raw hex values when a token exists.
4. Preserve route, state, loading, empty, error, focus, and responsive behavior identified by the brief.
5. Resolve stale/conflicting mappings and missing required props before editing. Read cited source files when the bounded brief omits needed details.
6. Treat inferred story IDs and host-supplied mappings as evidence, not rendered verification. Run the actual project tests.

## Handoff

Before editing, state the components and tokens you will reuse. After editing, cite files changed, evidence followed, checks run, and any design assumptions that remain.
