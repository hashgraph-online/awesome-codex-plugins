---
title: Framework Conventions
impact: MEDIUM
tags: nextjs, expo, framework, special-files
---

**Rule**: Framework special files must follow the exact naming the framework expects. Do not rename or restyle them.

### Next.js App Router

These files must be lowercase — the framework will not recognise them otherwise:

| File | Purpose |
|------|---------|
| `page.tsx` | Route page component |
| `layout.tsx` | Shared layout wrapper |
| `loading.tsx` | Suspense loading UI |
| `error.tsx` | Error boundary |
| `not-found.tsx` | 404 page |
| `route.ts` | API route handler |
| `middleware.ts` | Request middleware (project root) |
| `default.tsx` | Parallel route fallback |

### Incorrect

```
app/dashboard/
├── Page.tsx          # PascalCase — won't work
├── Layout.tsx        # PascalCase — won't work
└── Error.tsx         # PascalCase — won't work
```

### Correct

```
app/dashboard/
├── page.tsx
├── layout.tsx
└── error.tsx
```

### Expo Router

Expo Router uses file-based routing. Custom files alongside routes should follow `kebab-case`:

```
app/
├── page.tsx
├── dashboard-chart.tsx      # Colocated component (kebab-case)
└── use-dashboard-data.ts    # Colocated hook (kebab-case)
```

### Detection

Check `package.json` for `next` or `expo` in dependencies to determine which framework conventions apply.
