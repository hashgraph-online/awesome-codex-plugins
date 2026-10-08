---
title: Anti-Patterns
impact: HIGH
tags: anti-patterns, catch-all, nesting, barrels, circular
---

**Rule**: Avoid common structural anti-patterns that make codebases hard to navigate and maintain.

### Catch-All Files

Avoid generic `utils.ts`, `helpers.ts`, `common.ts` — they accumulate unrelated helpers and give no clue where anything lives. Split by domain (`lib/date.ts`, `lib/currency.ts`).

### Deep Nesting

Keep directory depth under 4 levels. Use descriptive names instead of deeper nesting.

```
# Bad
src/features/auth/components/forms/fields/inputs/text-input.tsx

# Good
src/features/auth/components/auth-text-field.tsx
```

### Barrel Files

Avoid `index.ts` re-export files; import directly from source modules. Acceptable at package entry points, where a public API boundary is intentional.

### Circular Dependencies

Watch for modules that import each other directly or through a chain. Common signs:
- Runtime errors about undefined imports
- Barrel files that re-export from modules that import back from the barrel
- Feature A importing from Feature B and vice versa

Fix by extracting shared code into a separate module that both features import from.

### Separated Tests

Don't put all tests in a separate `__tests__/` directory. Colocate unit tests next to the code they test.

### Language Grouping in Monorepos

Group packages by domain, not by language.

```
# Bad
packages/typescript/
packages/go/

# Good
packages/auth/
packages/payments/
```
