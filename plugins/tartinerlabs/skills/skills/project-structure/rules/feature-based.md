---
title: Feature-Based Grouping
impact: MEDIUM
tags: feature, domain, frontend, grouping
---

**Rule**: Group by domain — all related code (components, hooks, services, tests) in one directory. Recommended for frontend projects.

### Structure

```
src/features/
├── auth/
│   ├── components/
│   ├── hooks/
│   ├── auth.service.ts
│   └── auth.test.ts
├── users/
│   ├── components/
│   ├── hooks/
│   └── users.service.ts
└── products/
    ├── components/
    └── products.service.ts
```

### Next.js App Router

Use route groups to organise by feature without affecting the URL:

```
app/
├── (auth)/
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── layout.tsx
├── (dashboard)/
│   ├── overview/page.tsx
│   ├── settings/page.tsx
│   └── layout.tsx
└── layout.tsx
```

### Monorepo Variant

```
apps/           # Applications
├── web/
├── api/
packages/       # Shared libraries (by domain, not language)
├── types/
├── utils/
└── ui/
```
