---
title: Framework Structure
impact: MEDIUM
tags: nextjs, expo, framework, app-router, file-based-routing
---

**Rule**: Follow framework-specific directory conventions. File-based routing frameworks require specific directory structures to function correctly.

### Next.js App Router

```
app/
├── layout.tsx              # Root layout (required)
├── page.tsx                # Home route
├── loading.tsx             # Loading UI
├── error.tsx               # Error boundary
├── not-found.tsx           # 404 page
├── (marketing)/            # Route group (no URL segment)
│   ├── about/page.tsx
│   └── pricing/page.tsx
├── dashboard/
│   ├── layout.tsx          # Nested layout
│   ├── page.tsx
│   └── @modal/             # Parallel route (named slot)
│       └── default.tsx
└── api/
    └── users/route.ts      # API route handler
```

Key conventions:
- `app/` is the root for all routes
- Route groups `(name)/` organise without affecting URLs
- Parallel routes `@name/` render multiple pages in the same layout
- `middleware.ts` lives at the project root, not inside `app/`

### Expo Router

```
app/
├── (tabs)/
│   ├── index.tsx           # First tab
│   └── settings.tsx        # Second tab
└── [id].tsx                # Dynamic route
```

Key conventions:
- `(name)/` for layout groups (tabs, drawers)
- `[param].tsx` for dynamic segments

> **Note**: Expo Router requires specific prefixes for certain files (e.g., layout files, not-found screens). These are framework-mandated — do not use `_` or `+` prefixes for your own files outside of what the framework requires.
