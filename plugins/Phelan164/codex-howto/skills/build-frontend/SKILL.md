---
name: build-frontend
description: Build or modify frontend interfaces using repository-native components while preserving accessibility, responsive behavior, state handling, and visual verification. Use for UI features, design implementation, forms, client-side defects, and frontend refactors; do not use for backend-only or infrastructure-only work.
---

# Build Frontend

## Domain contract

- Preserve the project’s framework, styling system, and component conventions.
- Do not invent API response fields or silently change backend contracts.
- Do not replace an established design system with custom one-off styling.
- Define loading, empty, error, success, and disabled states that the changed
  flow can reach.
- Keep semantic HTML, keyboard navigation, focus behavior, labels, and contrast in scope.
- Avoid speculative shared abstractions for a single component.
- Treat screenshots and mockups as visual references, not proof of interaction behavior.
- Do not claim visual verification unless the UI was rendered or inspected.

## Execute and verify

Read [references/verification.md](references/verification.md) for UI, accessibility, responsive, and browser verification. Load it when the task changes rendered behavior or interaction.

Reuse existing components and tokens, implement the smallest coherent change,
and prove behavior at the lowest useful layer. Prefer:

```text
component test → feature test → type/lint → build → visual/interaction check
```

If a command cannot run, report the exact blocker and what remains unverified.
