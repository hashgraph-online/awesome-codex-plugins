---
name: cometchat-react-v7-customization
description: "Theme and brand the React v7 UI Kit — light/dark mode, CSS custom-property design tokens, per-component style overrides. Triggers: 'change chat colors', 'dark mode chat', 'match my brand', 'customize cometchat theme', 'override message list styles'."
license: "MIT"
compatibility: "React >=18; @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react customization theming css-variables v7"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. Theming mechanism below is from the live v7 theming docs (see core `references/docs-map.md` → `/ui-kit/react/theming`). Status: **catalog-verified vs installed 7.1.0 (exports-only web-v7.json).** Fetch the full `--cometchat-*` token list from the theming **`.md` twin** (`{DOCS_BASE}/ui-kit/react/theming.md`, via `docs-map.md`) — do NOT bake it.

## Companion skills (read first)
- `cometchat-react-v7-core` — install, provider, `init→login→render`. This skill ASSUMES it.

## Use this skill when
Branding/theming: colors, fonts, light/dark mode, or per-component style overrides.

## Prerequisites & install
Covered by core. No new package.

## Customization mechanism (BAKED — v7)
- **Design tokens = CSS custom properties**, all prefixed `--cometchat-*`, scoped to the `.cometchat` wrapper.
- **Light/dark:** built-in `light` (default) and `dark`, selected via the `theme` prop on `CometChatProvider` and the `data-theme` attribute on the wrapper. Runtime switching via the `useTheme` hook.
- **Follow the OS theme:** the `theme` prop is `"light" | "dark"` only and defaults to `light` — there is **no `theme="system"`** and the kit does NOT read `prefers-color-scheme` (AUDIT-004). To follow the system light/dark setting, sync the `theme` prop to `window.matchMedia("(prefers-color-scheme: dark)")` (with a `change` listener, SSR-guarded). Recommended as the default for a fresh integration. Full recipe: `cometchat-react-v7-core/references/theming.md`.
- **Import order:** import your overrides AFTER the UI Kit styles (import UI Kit CSS ONCE at root).

```tsx
import { CometChatProvider, useTheme } from "@cometchat/chat-uikit-react";
import "./cometchat-overrides.css";   // AFTER the kit styles

<CometChatProvider theme="dark"><>{/* your chat UI */}</></CometChatProvider>
```
```css
.cometchat { --cometchat-font-family: "Inter", sans-serif; }             /* theme-INDEPENDENT tokens only */
.cometchat[data-theme="light"] { --cometchat-primary-color: #e91e63; }   /* per-theme COLOURS → data-theme attr */
.cometchat[data-theme="dark"]  { --cometchat-primary-color: #bb86fc; }
.cometchat-message-list { /* BEM class to scope tokens per component */ }
```
> **Per-theme COLOURS go on the `data-theme` element — NOT the bare `.cometchat` class (AUDIT-033).** `CometChatProvider` renders one wrapper `<div data-theme="light|dark" class="cometchat">` (compiled bundle: `jsx("div",{ "data-theme": internalTheme, className: "cometchat" })`), and the kit defines its tokens on `[data-theme=light]` / `[data-theme=dark]`. **But several components render their OWN nested `<div class="cometchat …">` with NO `data-theme`** — verified for `CometChatSearch` (also popovers / portaled surfaces). So a colour on the bare `.cometchat` class ALSO lands on that nested wrapper and **re-pins the base (light) value there**: in dark mode the search stays light while everything else goes dark. Scope per-theme colours to `.cometchat[data-theme="light"]` / `.cometchat[data-theme="dark"]` so the nested wrapper matches neither and **inherits** the provider's theme. Keep only theme-independent tokens (font-family, radii) on bare `.cometchat`. (Earlier docs claimed `[data-theme="dark"] .cometchat` matches nothing — that's wrong: it DOES match those nested wrappers. It's still not the right selector for brand tokens; use the `.cometchat[data-theme]` form above.) To retint a kit INTERNAL per theme, use the kit's own pattern — `[data-theme="dark"] .cometchat-message-list { … }`.

## What's swappable
- Global tokens on `.cometchat` (primary color, fonts, radii, spacing — fetch the full token names from the theming `.md` twin).
- Per-theme overrides via `[data-theme="..."]`.
- Per-component scoping via BEM classes (`.cometchat-conversations`, `.cometchat-message-list`, …).
- Exact token names/defaults: fetch the theming `.md` twin (`{DOCS_BASE}/ui-kit/react/theming.md`, via core `references/docs-map.md`) — do NOT bake the token table.

### Differentiating a nested surface — an opaque sub-surface needs its OWN var override (BAKED — verified vs 7.1.0)
**Rule (general).** A kit sub-surface that paints an OPAQUE background does NOT inherit a wrapper's background — its own opaque paint covers whatever the wrapper set. To differentiate a nested surface you MUST override THAT surface's own background CSS variable (scoped on an ancestor — it cascades into the variable, no internal-class override needed), not just set a background on the wrapper.

**The thread panel is the canonical case.** Verified in the 7.1.0 CSS: `.cometchat-message-list` paints `background: var(--cometchat-message-list-bg)` (default `var(--cometchat-background-color-03)`); `.cometchat-thread-header` and `.cometchat-message-composer` paint their own opaque `var(--cometchat-background-color-01)`. So the thread's message list renders `-03` — the SAME shade as the main list, and different from its own header/composer — and a background on the thread wrapper alone can't fix it (the list covers it). **Override the list's own token on the thread wrapper:**
```css
/* the div you wrap CometChatThreadHeader + thread CometChatMessageList + CometChatMessageComposer in */
.cc-thread-panel {
  --cometchat-message-list-bg: var(--cometchat-background-color-01); /* matches the thread header/composer; differs from the main list's -03 */
  border-left: 1px solid var(--cometchat-border-color-default, #e8e8e8); /* optional divider from the main pane (-default = neutral-300 = #e8e8e8 light / #383838 dark) */
}
```
`--cometchat-background-color-01` is `#ffffff` (light) / `#141414` (dark) and `-03` is `#f5f5f5` (light) / `#272727` (dark) — so the override visibly separates the thread list from the main list in BOTH themes while matching the thread header/composer. Same trick for any per-surface background: scope the surface's OWN token on the wrapper, never override the kit's internal `.cometchat-*` element classes (`core/references/anti-patterns.md` #7/#12/#16).

> **Tinting the thread HEADER specifically — use its dedicated token.** `.cometchat-thread-header` paints `background: var(--cometchat-thread-header-background, var(--cometchat-background-color-01, #fff))` (verified vs 7.1.0 — `dist/index.css:12727`; the token is NOT defined in `:root`, only referenced with that fallback chain). So if you want to give the thread HEADER its own tint (a different shade from the list/composer, e.g. a subtly darker panel header), set `--cometchat-thread-header-background` directly on the thread wrapper — cleaner and more targeted than leaning on the `-01` fallback:
> ```css
> .cc-thread-panel {
>   --cometchat-message-list-bg: var(--cometchat-background-color-01);  /* REQUIRED — repaints the thread LIST (opaque, covers the wrapper) */
>   --cometchat-thread-header-background: var(--cometchat-background-color-02);  /* OPTIONAL — tints ONLY the thread header, independent of the list */
> }
> ```
> The `--cometchat-message-list-bg` override above is still **required** — the header token only paints the header; it does not touch the opaque message list. Use `--cometchat-thread-header-background` only when you want the header a *different* shade from the list; if you want them to match, the header already inherits `-01` and needs no override.

## Structural customization — view slots & composition (beyond tokens)
Theming changes how it LOOKS (tokens); changing WHAT renders is **view slots** + composition, not CSS. Every list/message component exposes view-slot props to inject custom UI **IN** the component (never as a sibling on top): e.g. Conversations `headerView` / `searchView`; MessageHeader `trailingView` / `auxiliaryButtonView`; MessageList `headerView` / `footerView`; Composer `auxiliaryButtonView` / `headerView`. Baked slot map: `cometchat-react-v7-core/references/component-props.md`. For the exhaustive per-component slot list, fetch the component's `.md` twin (`core/references/docs-map.md`) — do NOT read `.d.ts`. (Custom message **bubbles** are a separate capability — the message **plugin** architecture; see `cometchat-react-v7-features` + `COVERAGE.md`.)

## Common pitfalls (BAKED)
- Importing UI Kit CSS more than once, or overrides BEFORE the kit styles (specificity lost). Hardcoding hex in components instead of tokens. Assuming v6 theme classes — v7 uses `--cometchat-*` tokens + `data-theme`; fetch current names.
- **Writing a per-theme override as `[data-theme="dark"] .cometchat { … }` — it matches NOTHING and silently no-ops.** The provider puts `data-theme` and `class="cometchat"` on the SAME div, so there is no `.cometchat` nested inside a `[data-theme]` ancestor. Use `.cometchat[data-theme="dark"]` (same element) for brand tokens, or `[data-theme="dark"] .cometchat-<bem>` (ancestor + kit-internal descendant, the kit's own pattern) to retint an internal. (Verified vs 7.1.0.)
- **Hand-write brand/per-theme overrides — do NOT put per-theme tokens (colors, background, font) on bare `:root` (AUDIT-049/057).** A background or font pinned on `:root` has LOWER specificity than the kit's own `.cometchat[data-theme]` tokens, so it either loses (font silently doesn't apply) or forces the light value even in dark mode (breaks the OS-follow default, AUDIT-004/033). Scope every per-theme token to `.cometchat[data-theme="light"]` / `.cometchat[data-theme="dark"]` (theme-independent tokens like radii can stay on bare `.cometchat`). Theming is the SKILL's job — hand-write the scoped CSS (there is no CLI codegen for it).
- **Setting a background on a WRAPPER to differentiate a nested surface, and expecting it to show.** An opaque kit sub-surface (the message list paints its own `--cometchat-message-list-bg`) covers the wrapper background — the wrapper bg only shows through non-opaque children. To differentiate the sub-surface, override THAT surface's own token (above), never the wrapper alone and never its internal `.cometchat-*` class. This is why the thread message-list keeps looking undifferentiated from the main list even after a thread-wrapper background is set (AUDIT-020/024).
- **Assuming the kit follows the OS theme — it doesn't.** `theme` defaults to `light` and there's no `theme="system"`; a plain integration ignores the user's OS dark-mode setting. Sync to `prefers-color-scheme` if OS-follow is wanted (AUDIT-004).

## Verify it works
Your theme / `--cometchat-*` overrides apply in the running app (colors, light/dark), and the kit CSS is imported once at the app root.

**Close (after it builds):** end with the shared 3-option selectable menu and WAIT for the pick — **① add another feature** (suggest a few not-yet-wired) · **② customize theming** (further tweaks) · **③ test it manually** (stop; let the user check). Tailor suggestions to what's not yet done. Same contract as the `cometchat-react-v7-core` close (`RULES.md` §19).
