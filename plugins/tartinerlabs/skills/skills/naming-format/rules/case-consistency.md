---
title: Case Consistency
impact: HIGH
tags: naming, kebab-case, files, directories, casing
---

**Rule**: Use `kebab-case` for all files and directories. Detect the project's dominant convention first and flag outliers.

### Files

| Type | Convention | Example |
|------|------------|---------|
| All files | `kebab-case.ts` | `user-profile.ts` |
| Components | `kebab-case.tsx` | `user-profile.tsx` |
| Hooks | `use-*.ts` | `use-user.ts` |
| Directories | `kebab-case` | `user-profile/` |

### Incorrect

```
src/
├── UserProfile.tsx
├── useAuth.ts
├── APIClient.ts
├── userTypes.ts
└── MyComponent/
```

### Correct

```
src/
├── user-profile.tsx
├── use-auth.ts
├── api-client.ts
├── user.types.ts
└── my-component/
```

### Detection

Before flagging violations, count existing files to identify the dominant convention. If the project consistently uses a different convention (e.g., PascalCase for components), respect it and flag files that break *that* convention instead.
