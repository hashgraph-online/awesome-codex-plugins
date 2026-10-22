---
name: cometchat-angular-v5-customization
description: "Brand and customize the CometChat Angular UI Kit — CSS variable tokens, light/dark via ThemeService, localization, date/time formats, global config, and swapping component regions with ng-template. Triggers: 'change the chat colours', 'match my brand angular', 'dark mode', 'translate the chat', 'change the date format', 'custom avatar in the list'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular customization theming v5 branding dark-mode localization tokens"
---

> **Ground truth:** `@cometchat/chat-uikit-angular@5` (5.1.0–5.2.0 verified). Theme tokens, `ThemeService` and the global config are FETCHED from `{DOCS_BASE}/ui-kit/angular/customization/theming.md`, `/customization/global-config.md`, `/customization/localization.md`, `/customization/date-time-formatting.md` and `/message-bubble-styling.md` — base + paths in `cometchat-angular-v5-core/references/docs-map.md`. CSS variable names are version-pinned; never invent a token.

## Companion skills (read first)
- `cometchat-angular-v5-core` — install and `references/theming.md` for the token basics. Assumed.
- `cometchat-angular-v5-components` — view slots, when the change is structural rather than visual.

## Use this skill when
Changing how the kit **looks or reads**: colours, fonts, dark mode, language, date formats, or replacing a region's markup.

## Pick the smallest lever
| Want | Use | Cost |
| --- | --- | --- |
| Different colours / spacing | CSS variables | one stylesheet |
| Light ↔ dark | `ThemeService` | one line |
| Different language | `CometChatLocalize` | config |
| Different date format | per-component `*DateTimeFormat` inputs | one input |
| Different markup in a region | `*View` slot + `ng-template` | a template |
| Different behaviour | not customization — see `features` or `components` | — |

Reach for the first that works. Replacing a whole region to change a colour throws away selection, presence and receipts.

## CSS variables
Every visual is a `--cometchat-*` custom property. Override wherever it cascades — usually `styles.css`.
```css
:root {
  --cometchat-primary-color: #6851D6;
  --cometchat-border-color-default: #DCDCDC;
  --cometchat-text-color-primary: #141414;
}
```
Scope to part of the app by setting them on a wrapper instead of `:root`. Full token list: `{DOCS_BASE}/ui-kit/angular/customization/theming.md`.

Never target generated class names with descendant selectors — they change between releases. Never use `!important`; if a token is not applying, the kit stylesheet is not registered (`angular.json` → `styles`) or your rule is not in the cascade path.

## Light / dark — ThemeService does it all
```ts
import { Component, inject } from '@angular/core';
import { ThemeService } from '@cometchat/chat-uikit-angular';

@Component({ selector: 'app-root', standalone: true, template: '<router-outlet />' })
export class AppComponent {
  constructor() { inject(ThemeService).initFromPreference(); }
}
```
That single call respects the OS `prefers-color-scheme`, applies `data-theme` to `<html>` via the `DOCUMENT` token (SSR-safe), and keeps its own `matchMedia` listener so the UI follows the OS live.

> ⚠️ **It does NOT persist, despite its docstrings.** Verified against shipped 5.1.0: `initFromPreference()` claims to read `localStorage` first and `setTheme()`/`toggleTheme()` claim to persist, but the class never touches `localStorage` — a manual toggle is lost on reload. If the user needs a toggle that survives reload, add persistence **around** the service (`cometchat-angular-v5-core/references/theming.md`) rather than replacing it; a second `matchMedia` listener will drift from `currentTheme()`.

Toggle: `themeService.toggleTheme()` — do not compute the next value yourself. Set a specific mode: `themeService.setTheme('dark')`. Read: `themeService.currentTheme()` — a signal, so it works directly in templates.

> **Divergence from the docs.** `{DOCS_BASE}/ui-kit/angular/customization/theming.md` documents `setTheme()`, `toggleTheme()` and setting `data-theme` by hand, but does **not** mention `initFromPreference()` or following the OS `prefers-color-scheme`. `initFromPreference()` is real and verified against the installed 5.1.0 kit — prefer it over a hand-written `matchMedia` listener. Do not "correct" it away because the guide omits it; the omission is a docs gap, not evidence the method is wrong.

> Do **not** hand-roll a `matchMedia('(prefers-color-scheme: dark)')` listener. That is the React recipe; React's kit cannot read the OS. Angular's can, and duplicating it creates state that drifts from `currentTheme()`.

## Localization
`CometChatLocalize` ships 19 languages. Set the language once at startup; the `TranslatePipe` and `getLocalizedString()` read from it. To override individual strings or add a language, fetch `{DOCS_BASE}/ui-kit/angular/customization/localization.md` — the override shape is version-specific and worth reading rather than guessing.

## Date & time formats
Per-component inputs, not global CSS: `lastMessageDateTimeFormat` (conversations), `messageSentAtDateTimeFormat` (search), `callInitiatedDateTimeFormat` (call logs), `lastActiveAtDateTimeFormat` (message header). Pipes `CalendarDatePipe`, `MessageDatePipe` and `ConversationDatePipe` are exported if you need the same formatting in your own markup.

## Global config
`COMETCHAT_GLOBAL_CONFIG` is an injection token for app-wide kit defaults. Prefer it over repeating the same input on every component instance. Details: `{DOCS_BASE}/ui-kit/angular/customization/global-config.md`.

## Structural changes
Replacing markup rather than styling it is a **view slot** — `itemView`, `titleView`, `subtitleView`, `leadingView`, `trailingView`, `headerView`, `emptyView`, `errorView`, `loadingView`. See `cometchat-angular-v5-components`. Override the smallest slot that does the job.

## Common pitfalls
1. **Hand-rolling OS theme detection** — `ThemeService.initFromPreference()` already does it.
2. **Replacing `itemView` for a colour change** — loses selection, presence and receipts.
3. **Styling generated class names** — breaks on the next kit release.
4. **`!important` wars** — the stylesheet is not registered, or the rule is out of cascade.
5. **Two theme sources** — `ThemeService` plus your own `data-theme` writer; they drift.

## Verify it works
Brand colours apply in both themes · dark mode survives a reload ONLY if you persisted the choice yourself (the kit does not — see the warning above); without that, a reload falls back to the OS setting · the OS theme is respected on first load · localized strings render · overridden regions keep click, presence and receipts working.

## Explain what you built (REQUIRED close)
Tell the developer what changed, naming the files: what you themed — which tokens changed and whether light/dark follows the OS. Flag anything dev-only as dev-only, and say what you did **not** touch — this is additive.

**Then offer these THREE options as a SELECTABLE choice and WAIT for the pick — never auto-continue (`RULES.md` §19):**
1. **Add another feature** → a feature from `features.angular-v5.json`, or deeper structural customization via view slots. **Never offer an `auto` entry** (reactions, mentions, receipts, typing, media) — those are core in v5 and already on.
2. **Add a feature** (search, calls, polls, AI) → `cometchat-angular-v5-features`.
3. **Test it manually** → do nothing further; hand back so the user runs it.
