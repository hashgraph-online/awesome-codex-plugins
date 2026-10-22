---
name: cometchat-react-v7-patterns
description: "Framework wiring for the React v7 UI Kit across Vite, Create React App, Next.js, React Router (incl. Remix), and Astro — provider placement, env vars, routing, SSR/islands and build pitfalls. Triggers: 'cometchat with vite', 'cometchat in next.js', 'cometchat in react router', 'cometchat in remix', 'cometchat in astro', 'env vars not working', 'cometchat provider setup', 'SSR window is not defined'."
license: "MIT"
compatibility: "React >=18; Vite >=4 / CRA / Next.js >=13 / react-router(-dom) ^6–7 / Astro >=3 (@astrojs/react); @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react patterns vite nextjs cra react-router remix astro provider env ssr v7"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. Framework mechanics (env prefixes, SSR) are baked framework knowledge; kit symbols come from `cometchat-react-v7-core`. Status: **catalog-verified vs installed 7.1.0 (exports-only web-v7.json).**

## Companion skills (read first)
- `cometchat-react-v7-core` — install, provider, `init→login→render`. This skill ASSUMES it.

## Use this skill when
Wiring the UI Kit into a specific React toolchain, or debugging env/routing/SSR issues.

## Prerequisites & install
Covered by core. No new package.

## Framework wiring (BAKED — the delta per toolchain; full recipe = fetch the docs integration page)
- **Vite:** env in `.env` with `VITE_` prefix; read via `import.meta.env.VITE_COMETCHAT_*`. init/login in an app-startup effect; mount `CometChatProvider` above the chat routes. **Brownfield gotcha (AUDIT-037/066):** if the `vite/client` types aren't wired, `import.meta.env` is untyped → strict-TS build fails `TS2339: Property 'env' does not exist on ImportMeta`. Scaffolds wire `vite/client` differently by Vite version — older ones ship `src/vite-env.d.ts` (`/// <reference types="vite/client" />`), newer ones (Vite 8+) put `"vite/client"` in the `types` array of `tsconfig.app.json`. **Don't assume either is present — CHECK, then ensure `vite/client` is referenced:** add `/// <reference types="vite/client" />` at the top of the env-reading file (self-contained, works regardless of Vite version), or add `"vite/client"` to `tsconfig.app.json` `compilerOptions.types`, or create `src/vite-env.d.ts`.
- **Create React App:** env with `REACT_APP_` prefix; read via `process.env.REACT_APP_*`.
- **Next.js:** client-only kit — put init/login + `CometChatProvider` in a Client Component (`"use client"`); env in `.env.local` with `NEXT_PUBLIC_*`. Guard browser-only code so it never runs during SSR (App Router AND Pages Router).
- **React Router / Remix:** two modes — **v6 library mode** (routing inside a Vite/CRA app, no SSR, `VITE_` env) wires like Vite; **v7 framework mode** (SSR, the Remix successor — a legacy `@remix-run/react` app maps here) has Next-like SSR concerns → render the chat client-only (client guard / `clientLoader` / a `<ClientOnly>`), `VITE_` env. Provider above the routed outlet.
- **Astro:** the kit is a React **island** — mount it with `client:only="react"` (never SSR it); env with `PUBLIC_` prefix (`import.meta.env.PUBLIC_COMETCHAT_*`). One island owns init/login + provider + chat.
- Keep `CometChatProvider` at a stable ancestor so init/login survive navigation (see `-placement`).
> **Full per-framework recipe:** fetch the docs integration page via `cometchat-react-v7-core/references/docs-map.md` — `integration-react` · `integration-nextjs` · `integration-react-router` · `integration-astro` (+ the `next-*` / `react-router-*` / `astro-*` layout recipes). Bake only the deltas above; fetch the rest.

## Framework pitfalls (BAKED)
- **SSR frameworks (Next.js · React Router v7 framework mode · Astro):** `window is not defined` / hydration errors when the kit renders on the server → render the chat **client-only** (`"use client"` in Next; `client:only="react"` in Astro; a client guard / `clientLoader` in React Router v7) and defer init to `useEffect`/the browser.
- **Astro:** using `client:load`/`client:visible` (they SSR the component first) instead of `client:only="react"` → server-render crash.
- Wrong env prefix for the toolchain (Vite/React-Router `VITE_` · CRA `REACT_APP_` · Next `NEXT_PUBLIC_` · Astro `PUBLIC_`) → values are `undefined` at runtime.
- Importing UI Kit CSS in multiple entry points (import once at root).
- Auth key shipped to the client in production — use server-side token exchange (`RULES.md`).

## Common pitfalls (BAKED)
See above; also `version_conflict` STOP (v6 installed) per core.

## Verify it works
The app builds and chat renders on your framework (Vite / Next / React Router / Astro) with the correct env prefix and SSR guards (`"use client"` / `ssr:false` where needed).
