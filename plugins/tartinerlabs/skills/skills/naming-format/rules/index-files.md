---
title: Index Files
impact: HIGH
tags: index, barrel, re-export, tree-shaking, imports
---

**Rule**: Avoid barrel files (`index.ts` with re-exports). They hurt tree-shaking, slow down TypeScript and bundlers, and create circular dependency risks. Use direct imports instead.

### Incorrect

```ts
// components/index.ts — barrel file
export { Button } from './button'
export { Card } from './card'
export { Modal } from './modal'
export { Avatar } from './avatar'

// usage — hides the actual source
import { Button, Card } from '@/components'
```

### Correct

```ts
// Direct imports — no barrel file needed
import { Button } from '@/components/button'
import { Card } from '@/components/card'
```

### Why Barrel Files Are Harmful

- **Tree-shaking**: Bundlers may include unused exports from the barrel
- **TypeScript performance**: Large barrel files slow down type checking
- **Circular dependencies**: Barrels that re-export from modules that import back from the barrel cause runtime errors
- **Editor navigation**: "Go to definition" lands on the barrel, not the source

### Exception

Package entry points (`packages/ui/index.ts`) where a public API boundary is intentional. These define what consumers can import and are part of the package contract.

### Fix

1. Delete the `index.ts` barrel file
2. Update all imports to point directly at source files
3. Verify no broken imports remain
