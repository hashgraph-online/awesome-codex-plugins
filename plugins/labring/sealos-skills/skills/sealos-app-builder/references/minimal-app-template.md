# Minimal App Template

Use this reference when a Sealos app needs the smallest stable integration pattern.

## Recommended shape

Put the Sealos integration in one client-only root provider.

## Install first

Install the official SDK package before copying any template code:

```bash
pnpm add @labring/sealos-desktop-sdk
```

Equivalent commands:

```bash
npm install @labring/sealos-desktop-sdk
yarn add @labring/sealos-desktop-sdk
```

The provider should own:

1. SDK initialization.
2. Session loading.
3. Language loading.
4. Desktop availability state.
5. Optional language-change subscription.

## Recommended state shape

```ts
type SealosContextValue = {
  session: SessionV1 | null;
  language: string;
  loading: boolean;
  error: string | null;
  isInSealosDesktop: boolean;
};
```

## Root integration rules

1. Call `createSealosApp()` once.
2. Fetch `getSession()` and `getLanguage()` early.
3. Store the results centrally.
4. Clean up listeners on unmount.
5. Show a clear fallback if Desktop is unavailable.

## Best practices

### Use a single provider

Prefer one provider or store near the app root over repeated per-page initialization.

### Make the fallback explicit

If the app is opened outside Sealos Desktop, set:

1. `isInSealosDesktop = false`
2. `loading = false`
3. a friendly error or info message

### Keep the business layer unaware of iframe details

Page-level components should consume:

1. `session`
2. `language`
3. `isInSealosDesktop`

They should not care about raw `postMessage` plumbing.

## Starter file

Use one of these starter files:

1. [../assets/templates/react/sealos-provider.tsx](../assets/templates/react/sealos-provider.tsx) for React.
2. [../assets/templates/vue/use-sealos.ts](../assets/templates/vue/use-sealos.ts) for Vue.

## Next.js App Router

If the app uses Next.js App Router, read [nextjs-app-router.md](nextjs-app-router.md) and keep the provider inside a client component that is mounted from the root layout.
