# Next.js App Router

Use this reference when the target app uses Next.js App Router and you need a concrete placement example for the Sealos integration.

## Recommended structure

Use a small client-only wrapper for providers, then mount it from `app/layout.tsx`.

Example layout:

```text
app/
  layout.tsx
  providers.tsx
components/
  sealos-provider.tsx
```

## Why this structure works

1. `app/layout.tsx` can remain a server component.
2. `app/providers.tsx` becomes the client boundary for SDK initialization.
3. `components/sealos-provider.tsx` contains the reusable Sealos context logic.

## Minimal example

### `components/sealos-provider.tsx`

Use [../assets/templates/react/sealos-provider.tsx](../assets/templates/react/sealos-provider.tsx).

### `app/providers.tsx`

```tsx
'use client';

import type { ReactNode } from 'react';
import { SealosProvider } from '@/components/sealos-provider';

export function Providers({ children }: { children: ReactNode }) {
  return <SealosProvider>{children}</SealosProvider>;
}
```

### `app/layout.tsx`

```tsx
import type { ReactNode } from 'react';
import { Providers } from './providers';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

## Rules

1. Do not call `createSealosApp()` directly from `app/layout.tsx` if it is a server component.
2. Keep SDK initialization in a client component such as `providers.tsx` or the provider itself.
3. Expose `session`, `language`, and `isInSealosDesktop` through context or a store so route segments stay simple.
