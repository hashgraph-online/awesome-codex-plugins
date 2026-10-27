# theming — CSS at the core level (React v7)

Import the UI Kit CSS ONCE at the app root; theme via `--cometchat-*` variables. v7 also supports a `theme` prop on `CometChatProvider` and a `useTheme` hook with `light`/`dark` + `data-theme`.

```tsx
// import once at the highest level (main.tsx / app/layout.tsx / global css)
import "@cometchat/chat-uikit-react/styles";   // v7.1.0 CSS entry (package exports "./styles" -> dist/index.css)
```
The CSS-only `./styles` export has no type declaration, so on TypeScript 6 (`noUncheckedSideEffectImports` defaults ON — it's not a `strict` thing; opt-in on 5.6–5.9) that import errors with **TS2882 "Cannot find module or type declarations for side-effect import of '@cometchat/chat-uikit-react/styles'."** (verified vs TS 6.0.3). Ship this ambient declaration as a REAL file the app can copy — `src/cometchat-styles.d.ts` (any `.d.ts` picked up by `tsconfig` `include`) — so the import type-checks (AUDIT-013). **Never name it after an existing `.ts` module** (e.g. `src/cometchat.d.ts` next to a `src/cometchat.ts` init file): TypeScript treats `X.d.ts` beside `X.ts` as that module's own output and skips it, so TS2882 comes back (verified vs TS 6.0.3, Vite react-ts):
```typescript
// src/cometchat-styles.d.ts — lets TS accept the CSS-only "./styles" side-effect import (TS2882 otherwise)
declare module "@cometchat/chat-uikit-react/styles";
```
```css
/* theme-INDEPENDENT tokens (identical in light & dark) may sit on the bare class */
.cometchat { --cometchat-font-family: "Inter", sans-serif; }
/* theme-DEPENDENT tokens (every colour) MUST be scoped to the data-theme ATTRIBUTE,
   NOT the bare `.cometchat` class — see the gotcha below. */
.cometchat[data-theme="light"] { --cometchat-primary-color: #6851d6; }
.cometchat[data-theme="dark"]  { --cometchat-primary-color: #bb86fc; }
```
- **Scope colour tokens to `data-theme`, not bare `.cometchat` (AUDIT-033).** The provider renders `<div data-theme="light|dark" class="cometchat">`, but several components (verified: `CometChatSearch`; also popovers/portaled surfaces) render their OWN nested `<div class="cometchat …">` **with NO `data-theme`**. A colour token on the bare `.cometchat` class therefore ALSO matches that nested wrapper and **re-pins the light value on its subtree** — so in dark mode the search (etc.) stays light while everything else goes dark. Put per-theme colours on `.cometchat[data-theme="light"]` / `.cometchat[data-theme="dark"]`: the nested wrapper matches neither and simply **inherits** the provider's theme. Use `.cometchat[data-theme="dark"]` (the SAME element) — NOT `[data-theme="dark"] .cometchat` (a descendant that matches nothing → silent no-op). To retint a kit internal per theme, use `[data-theme="dark"] .cometchat-<bem>` (the kit's own convention). Depth: `cometchat-react-v7-customization`.
- Never target internal class names (e.g. `.cometchat-message-bubble__wrapper`) — not public API, changes between versions. Use `--cometchat-*` variables (or documented BEM classes for per-component scoping).
- Import overrides AFTER the kit CSS.
- **Per-surface background tokens.** Some surfaces paint an opaque background from their OWN token, so a wrapper background can't reach them — override that surface's token instead. Two common ones (verified vs 7.1.0): the message list paints `--cometchat-message-list-bg` (default `-03`, `dist/index.css:4243`) and the thread header paints `--cometchat-thread-header-background` (falls back to `-01`, `dist/index.css:12727`; not set in `:root`, so setting it directly is the clean way to tint the thread header specifically). Differentiating the thread panel from the main list uses exactly this — see the thread recipe in `cometchat-react-v7-customization` (message-list-bg is the required step; thread-header-background is an optional header-only tint).

## Follow the system (OS) light/dark theme (recommended default)
The `theme` prop is `"light" | "dark"` and **defaults to `light`** — the UI Kit does **NOT** read the OS `prefers-color-scheme` and there is **no `theme="system"`** (AUDIT-004). For a fresh integration, sync the theme to the OS by default (least surprise) with a small SSR-guarded hook, and pass it to `CometChatProvider`:

```tsx
import { useEffect, useState } from "react";
import { CometChatProvider } from "@cometchat/chat-uikit-react";

function useSystemTheme(): "light" | "dark" {
  const read = () =>
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const [theme, setTheme] = useState<"light" | "dark">(read);   // SSR: renders "light", corrects on hydrate
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setTheme(mq.matches ? "dark" : "light");
    mq.addEventListener("change", onChange);                    // live-updates when the OS theme flips
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return theme;
}

// <CometChatProvider theme={useSystemTheme()}> … </CometChatProvider>
```
For an explicit user toggle instead of OS-follow, use `useTheme()` (`{ theme, setTheme }`). Next.js/SSR: `window.matchMedia` must stay guarded — see `references/ssr.md`.

Full theming depth (token list, per-component BEM, dark mode switching): `cometchat-react-v7-customization`.
