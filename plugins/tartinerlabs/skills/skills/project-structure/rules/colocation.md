---
title: Colocation
impact: HIGH
tags: colocation, proximity, organisation
---

**Rule**: Place code as close to where it's relevant as possible. Things that change together should be located together.

### Incorrect

```
src/
├── components/
│   └── user-profile.tsx
├── hooks/
│   └── use-user.ts
├── types/
│   └── user.ts
└── tests/
    └── user-profile.test.tsx
```

### Correct

```
src/features/users/
├── user-profile.tsx
├── user-profile.test.tsx
├── use-user.ts
└── user.types.ts
```

### Next.js App Router

Colocate components with the route that uses them:

```
app/dashboard/
├── page.tsx
├── dashboard-chart.tsx
├── dashboard-stats.tsx
└── use-dashboard-data.ts
```

### Where to Put Things

| Type | Location |
|------|----------|
| Shared types | `types/` or `packages/types/` |
| Utilities | `lib/` or `utils/` (split by domain) |
| Config | `config/` or root |
| Unit tests | Colocate: `foo.test.ts` next to `foo.ts` |
| E2E tests | `e2e/` or `tests/e2e/` |
| Mocks/fixtures | `__mocks__/` or `test/mocks/` |
