---
title: Export Naming
impact: HIGH
tags: exports, components, hooks, constants, types, naming
---

**Rule**: Use consistent naming conventions for exported symbols based on their role.

### Conventions

| Export type | Convention | Example |
|-------------|------------|---------|
| React components | `PascalCase` | `UserProfile` |
| Hooks | `camelCase` with `use` prefix | `useUser` |
| Utility functions | `camelCase` | `formatDate` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Types / interfaces | `PascalCase` | `UserProfile` |
| Enums | `PascalCase` name, `PascalCase` members | `UserRole.Admin` |

### Incorrect

```tsx
// user-profile.tsx
export function userProfile() { ... }     // Should be PascalCase
export const User_Profile = () => { ... } // Snake_Case component

// use-auth.ts
export function UseAuth() { ... }         // Should be camelCase

// api.constants.ts
export const maxRetries = 3               // Should be UPPER_SNAKE_CASE
export const apiBaseUrl = '/api'           // Should be UPPER_SNAKE_CASE

// user.types.ts
export type userProfile = { ... }         // Should be PascalCase
```

### Correct

```tsx
// user-profile.tsx
export function UserProfile() { ... }

// use-auth.ts
export function useAuth() { ... }

// api.constants.ts
export const MAX_RETRIES = 3
export const API_BASE_URL = '/api'

// user.types.ts
export type UserProfile = { ... }
```
