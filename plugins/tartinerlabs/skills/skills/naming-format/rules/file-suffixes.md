---
title: File Suffixes
impact: HIGH
tags: suffixes, test, types, schema, config
---

**Rule**: Use consistent suffixes to indicate a file's role. Detect which suffix pattern the project already uses and enforce consistency.

### Conventions

| Role | Suffix | Example |
|------|--------|---------|
| Unit tests | `*.test.ts` or `*.spec.ts` | `user-profile.test.ts` |
| E2E tests | `*.e2e.ts` | `checkout.e2e.ts` |
| Type definitions | `*.types.ts` | `user.types.ts` |
| Validation schemas | `*.schema.ts` | `user.schema.ts` |
| Constants | `*.constants.ts` | `api.constants.ts` |
| Hooks (multiple) | `*.hooks.ts` | `auth.hooks.ts` |
| Configuration | `*.config.ts` | `database.config.ts` |

### Incorrect

Mixing suffix patterns within the same project:

```
src/
├── user.test.ts        # Uses .test.ts
├── auth.spec.ts        # Uses .spec.ts — inconsistent
├── userTypes.ts        # No suffix separator
├── UserSchema.ts       # PascalCase + no suffix separator
└── helpers.ts          # Generic name, no role suffix
```

### Correct

```
src/
├── user.test.ts
├── auth.test.ts        # Consistent with project pattern
├── user.types.ts
├── user.schema.ts
└── date.utils.ts       # Domain-specific utility
```

### Detection

Check the project for existing suffix patterns and follow the dominant one — in a `.spec.ts` codebase, a new `.test.ts` file is the finding. A project mid-migration will legitimately hold both: report the split and which side is the target, rather than renaming in both directions.
