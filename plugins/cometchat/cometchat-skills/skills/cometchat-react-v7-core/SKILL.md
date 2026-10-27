---
name: cometchat-react-v7-core
description: "Add CometChat chat to a React app end-to-end — detect the project, get & verify dashboard credentials, init→login→render with CometChatProvider, and the drop-in conversation UI. The core knowledge every other React v7 skill builds on. Triggers: 'add chat to my react app', 'integrate cometchat react', 'set up cometchat credentials', 'show conversations and messages'."
license: "MIT"
compatibility: "Node.js >=18; React >=18; Vite >=4 / CRA / Next.js; @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0); @cometchat/chat-sdk-javascript ^4.1.9"
metadata:
  author: "CometChat"
  version: "1.3.0"
  tags: "cometchat react core chat integration uikit v7 setup credentials"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7` + `@cometchat/chat-sdk-javascript@^4.1.9`. Symbols sourced from live v7 docs. This file is the THIN map loaded every run; deep detail is in `references/*` loaded ONLY when the task needs it. Anything marked **[v7-verify]** is a v6 carry-over to confirm against v7 docs/catalog before shipping.

<!-- core is the companion the other react v7 skills read; it has no Companion block of its own. -->

## Use this skill when
"add chat to my React app", "set up CometChat credentials", "integrate CometChat in React", "show a conversations + messages UI", "build a full chat app". An unscoped "add chat" means a **production-ready core chat surface** (a `CometChatConversations` list ↔ a message pane, wrapped in `CometChatErrorBoundary`, sized, affordances wired-or-hidden, mobile collapse) — NOT a bare two-pane demo, and NOT the whole combined app. See the golden path below. It **grows on request** (users/groups/calls tabs, a details/thread/search side panel, calls) to the full combined app — that recipe lives in `cometchat-react-v7-placement`.

## Install
`npm i @cometchat/chat-uikit-react@7 @cometchat/chat-sdk-javascript@4 dompurify` (keep the `@7`/`@4` major pins — a bare install resolves to `latest` and can pull the wrong major). `dompurify` is required by the kit — the docs install includes it. Voice/video calling also needs `@cometchat/calls-sdk-javascript` (see `cometchat-react-v7-features`).

## Setup & credentials (essentials — full detail: `references/setup-credentials.md`)
1. **Detect** React + bundler (Vite→`VITE_`, CRA→`REACT_APP_`, Next→`NEXT_PUBLIC_`/`.env.local`). Reuse existing `.cometchat`/env if present (skip re-setup).
2. **version_conflict — STOP** if a non-v7 UI Kit is installed; reconcile first (never mix majors — `RULES.md`).
3. **Credentials — OFFER the dashboard fetch FIRST, default to it** (never silently "paste it yourself", never defer to a "to finish, add them yourself" TODO — AUDIT-039). Reuse existing `.cometchat`/env if present (skip). Else offer both, defaulting to fetch: **(a) dashboard fetch (recommended)** — load the CLI on demand: `npx @cometchat/skills-cli@3 auth login`, **pick an EXISTING app** (`provision list --json`; **never auto-create**), `provision use --app-id <id> --json` returns the creds + writes a neutral `.cometchat/config.json` (NOT an env file); **(b) manual paste** — Dashboard → Credentials (dev-only Auth Key). **Then the SKILL writes the framework env (§4)** — the CLI stops at the fetch; framework detection, env-writing, and codegen are the SKILL's job, never the CLI's (AUDIT-059). Ask & wait if the user must choose or the CLI can't run. Full flow: `references/setup-credentials.md`.
4. **Write env** (correct prefix), gitignore it, never echo the Auth Key. Prod → server-side auth token, not the Auth Key.
5. **Authorize** = `init()` + `login()` resolve; auth error usually means wrong Region.

## Integration ordering (BAKED — invariant; docs: "init() must resolve before login()")
`init()` once at startup → `login(UID)` after init resolves (guard with the sync `CometChatUIKit.getLoggedInUser()`) → render inside `CometChatProvider`.

```tsx
import { CometChatUIKit } from "@cometchat/chat-uikit-react";
// initFromSettings (NOT the classic UIKitSettingsBuilder init) sets integrationSource="ai-agent"
// for telemetry attribution — and routes the Calls SDK through initFromSettings too (AUDIT-084).
await CometChatUIKit.initFromSettings({
  appId: import.meta.env.VITE_COMETCHAT_APP_ID,
  region: import.meta.env.VITE_COMETCHAT_REGION,
  credentials: { authKey: import.meta.env.VITE_COMETCHAT_AUTH_KEY }, // dev only; prod → server-minted auth token
  chatSDK: { presenceSubscription: { type: "ALL_USERS" } },         // = the classic subscribePresenceForAllUsers()
});                                                                  // must resolve first
if (!CometChatUIKit.getLoggedInUser()) await CometChatUIKit.login(UID);   // sync getter — capital "In"
```
> Init once + StrictMode double-init, concurrent-login guard, and the reusable provider: `references/lifecycle.md`.
> **Which UID?** `login()` needs a user that ALREADY EXISTS — never invent/hardcode a guessed one. ASK, or take one from Dashboard → **Users** (fresh apps seed `cometchat-uid-1…`). **Never suggest `superhero1..5` or any remembered "classic sample" UID (not seeded in modern apps); don't fabricate UIDs from memory — the only tentative suggestion is `cometchat-uid-1`, labelled "if this is a fresh app."** Prod → per-user auth token + `loginWithAuthToken`. Detail: `references/setup-credentials.md` §6.

## Component / API map (BAKED closed list)
Init/provider: `CometChatUIKit`, `UIKitSettingsBuilder`, `CometChatProvider`, `CometChatErrorBoundary` (wraps the surface — production must-have). Core-surface drop-ins: `CometChatConversations`, `CometChatMessageHeader`, `CometChatMessageList`, `CometChatMessageComposer`; wired affordances `CometChatThreadHeader`, `CometChatSearch`. Grow set (added on request): `CometChatUsers`, `CometChatGroups`, `CometChatCallLogs`, `CometChatGroupMembers`, `CometChatIncomingCall`.

## Hot-path props (BAKED — the golden path needs NO fetch)
The ~12 props you actually wire for "add chat". Do NOT fetch docs for these; do NOT read `.d.ts`.
- `CometChatConversations`: `onItemClick(conversation)` (select → drives the message pane) · `activeConversation` · `showSearchBar` (default `true`; wire `onSearchBarClicked`→`CometChatSearch` or set `false`) · `selectionMode` (default `"none"`) · `conversationsRequestBuilder` — **scope the list to the REQUEST**: a 1:1/DM-only ask → `new CometChat.ConversationsRequestBuilder().setLimit(30).setConversationType("user")` so the app's seeded groups don't show (`"group"` for groups-only); pass the builder INSTANCE, not `.build()`. **`.setLimit(n)` is REQUIRED on a custom builder** — without it the list renders the kit's "something went wrong" state (verified 7.2.0, AUDIT-245; STOPGAP: the docs' filter-recipe table omits it — remove this note once that docs recipe is fixed). See the data-scope note below.
- `CometChatMessageHeader`: `onItemClick` (open profile) · `showSearchOption` (default `true`) + `onSearchOptionClicked` → **open a SCOPED `CometChatSearch` (`uid`/`guid` of the current chat) in the side panel (in-chat message search, default-on; opt-out via `showSearchOption={false}`)** · `hideBackButton` (default `false`) + `onBack` (mobile → pop to list).
- `CometChatMessageList`: `onThreadRepliesClick(message)` → **open the thread panel (DEFAULT — threaded replies ship with a first-time "add chat")**; `hideReplyInThreadOption` ONLY if the user explicitly opts out of threads.
- `CometChatMessageComposer`: `placeholder` (default `"Type a message..."`); a plain send needs no props.
- `CometChatProvider`: `theme` (`"light"` default — no OS-follow; sync to `prefers-color-scheme`, see `references/theming.md`).
> **Stable props + view slots for the 4 drop-ins are BAKED in `references/component-props.md`** — use them: custom UI goes IN the component's slot (search → Conversations `headerView` / MessageHeader `trailingView`), NEVER as a sibling on top. Exhaustive/rare props or any OTHER component → fetch its `.md` twin via `references/docs-map.md`; NEVER read `node_modules/.d.ts`. Full catalog: `cometchat-react-v7-components`.


## Golden path — the production-ready CORE surface (default for an unscoped "add chat"; grows on request)
Setup → guarded init/login → wrap the app in `CometChatProvider` **inside `CometChatErrorBoundary`** → build the core surface: a `CometChatConversations` LIST ↔ a MESSAGE pane (`CometChatMessageHeader` + `CometChatMessageList` + `CometChatMessageComposer`) for the selected conversation, a small host state object coordinating {selected conversation, side view: thread | in-chat-search | none}, collapsing to one pane on mobile. Complete and wired but LEAN — NOT a bare two-pane demo, NOT the whole combined app. Reuse existing routing/layout/auth; add files + wiring only, never rewrite. Least-code = reach for the drop-ins/slots (HOW). **The compile-verified TSX + the required column CSS live in `references/layout.md` (sizing) and `cometchat-react-v7-placement/references/recipes.md` (the Core-surface recipe) — build from those; this entry stays the thin map.**

Wire every default-on affordance so nothing dead-ends, and keep these INVARIANTS:
- **Threads are DEFAULT** (ship with a first-time "add chat"). Wire `CometChatMessageList onThreadRepliesClick(m)` → a thread panel (`CometChatThreadHeader` + a thread `CometChatMessageList` + `CometChatMessageComposer`) with a close/back round-trip. **The thread list AND composer take BOTH the current target (`user` OR `group`, same as the main pane) AND `parentMessageId`; passing `parentMessageId` ALONE silently NEVER SENDS (AUDIT-060).** Set `hideReplyInThreadOption` only on explicit opt-out. **Differentiate the thread MESSAGE LIST** (not just the wrapper): scope `--cometchat-message-list-bg: var(--cometchat-background-color-01)` on the thread wrapper — the list paints its own opaque bg so a wrapper bg can't reach it (verified vs 7.1.0; recipe in `cometchat-react-v7-customization`).
- **Two searches, both default-on, both need the FULL round-trip (AUDIT-017).** GLOBAL conversation search over the LIST column (`CometChatConversations onSearchBarClicked` → `CometChatSearch`, no uid/guid — or `showSearchBar={false}`); IN-CHAT scoped search in the SIDE PANEL (`CometChatMessageHeader showSearchOption` default `true` → `onSearchOptionClicked` → `CometChatSearch` with the current `uid`/`guid`, mutually exclusive with the thread). Each renders a back button (`onBack`) you MUST wire to close + return, PLUS `onConversationClicked`/`onMessageClicked` to select the hit — a companion you open, you must also close. (Real server-side search may also need a Dashboard toggle — VERIFY.)
- **SIZE per the ONE standard — `references/layout.md`.** The kit fills its parent and ships its own `loadingView`/`emptyView`, so a broken-looking surface is a HOST container-sizing defect (a content-driven box), not a kit bug — two modes: static collapse (~0px sliver) and load-transition reflow (grows into place as content loads). Satisfy the 5 invariants: prepare/RESET the ancestor chain (`html,body,#root{height:100%;margin:0}` + undo the Vite/CRA/Next scaffold center+cap+pad, AUDIT-019/035) · pin the surface to a content-INDEPENDENT `100dvh` (never `min-height`/`auto`) · size COLUMNS with `min-height:0`/`overflow:hidden` (scroll, don't grow the parent) · let the kit loading state fill the pinned box · no `transform`/`filter` ancestors. The 2-column CSS is in `layout.md`; the 3-column/embedded/popup/sidebar recipes in `cometchat-react-v7-placement`. Keep `CometChatProvider` WRAPPING `.cc-app`, not inside it (the `.cometchat` wrapper breaks the row — AUDIT-036).
- **Match data scope to the REQUEST (AUDIT-038).** A 1:1/DM-only ask must NOT show the app's seeded groups — scope with the built-in `conversationsRequestBuilder` prop (pass the `CometChat.ConversationsRequestBuilder` INSTANCE, `.setLimit(30).setConversationType("user")` — `setLimit` required; `"group"` for groups-only; **reuse the prop, don't hand-roll a client-side filter**), and scope the selector to match (no Groups tab on a 1:1-only app). A generic unscoped "add chat" keeps BOTH. Example in `references/component-props.md`.
- **Theme:** the kit defaults to `light` and does NOT follow the OS (no `theme="system"`) — sync `CometChatProvider theme=` to `prefers-color-scheme` by default (`references/theming.md`, AUDIT-004).
- **Reuse built-in triggers — don't hand-roll buttons (AUDIT-006).** Wire the props components already expose; custom UI goes IN the component's view slot (search icon → Conversations `headerView` / MessageHeader `trailingView`), NEVER a sibling on top (slot map: `references/component-props.md`). Unclear prop → fetch its `.md` twin (`references/docs-map.md`), never the `.d.ts`.
- **`CometChatErrorBoundary` wraps the surface** (children required; optional `onError`/`fallbackView`/`componentName`) — a render error then shows a localized fallback + retry, not a blank white screen. It is NOT the initializer (init/login still happen first). Leave header call buttons + composer attach/emoji/voice as built-in defaults; do NOT turn on gated extensions/AI/plugins; do NOT add selector tabs / a details or scoped-search side panel / call logs / incoming call (those are the GROWTHS) unless asked — **but the thread panel IS part of the default.** **Prod auth: `loginWithAuthToken` with a per-user server-minted token; the Auth Key is dev-only** (`references/lifecycle.md`).

**Grows on request → the full combined app** (users/groups/calls **tabs**, a details/thread/scoped-search **side panel**, `CometChatIncomingCall` at root, **calls**, individual **features**) — the UNION of these growths. The compile-verified combined-app recipe (with the required column CSS + `CometChatErrorBoundary`) is baked in **`cometchat-react-v7-placement`**; build the grown app from it. A user who scopes DOWN (embed/popup/sidebar) → the matching `cometchat-react-v7-placement` variant.

## Deep references (load ONLY when the task needs them — keeps this file light on run)
- `references/setup-credentials.md` — detect, config reuse, version_conflict, dashboard creds, env, authorize.
- `references/lifecycle.md` — init-once + StrictMode, concurrent-login guard (`ensureLoggedIn`), get-current-UID (sync vs async), prod auth-token, logout, the full `CometChatProvider`.
- `references/layout.md` — **the ONE reflow-free-surface sizing standard** (the 5 invariants: prepared ancestor chain · pinned content-independent height · `min-height:0` columns · kit loading state inside the pinned box = NO load-transition reflow · no `transform`/`filter` ancestors). `placement` + `calls` reference it too — change sizing rules HERE.
- `references/ssr.md` — Next.js / Astro / React Router SSR safety (`"use client"`, `ssr:false`, `client:only`).
- `references/theming.md` — CSS import-once + `--cometchat-*` variables (depth: `cometchat-react-v7-customization`).
- Localization / RTL / accessibility → the cross-family **`cometchat-i18n`** + **`cometchat-a11y`** skills. Don't render a raw key (`group_info`) — the provider auto-wires localization. React theme tokens: `references/theming.md`.
- `references/anti-patterns.md` — the 15 real-bug anti-patterns (incl. `transform`/Tailwind overlay bug, container dimensions, **scaffold-boilerplate** = centered/capped/gutter-boxed chat (#15), **global-CSS-leak** = centered names / expanding header, **raw-i18n-key** rendering).
- `references/dependencies.md` — packages, major pins, `CometChat.*` SDK types, bundle-size cost transparency.
- `references/component-props.md` — **BAKED stable props + view slots** for the 4 drop-ins (where custom UI goes IN each component — search → Conversations `headerView`, MessageHeader `trailingView`, etc.).
- `references/docs-map.md` — intent → the exact docs `.md` twin to fetch (replaces reading `.d.ts`); **for a whole feature/task, its "Task guides (recipes)" section says to BUILD FROM the official guide + COMPARE your implementation against it (docs-maximal), then apply the hardening deltas.**
- Symptom → cause → fix (blank screen, SSR `window is not defined`, ~0px collapse, kit error state, empty lists, events not firing, `version_conflict`) → the **`cometchat-react-v7-troubleshooting`** skill.

> **Visual Builder (VCB) is out of scope.** If asked to integrate a VCB export, point to the CometChat Visual Builder docs (via `references/docs-map.md`); don't hand-roll a builder-export flow.

## Common pitfalls (top 4 — full list in `references/anti-patterns.md`)
version_conflict (v6 installed) · wrong Region or env prefix · Auth Key shipped to prod client · rendering/login before init resolves.

## Verify it works
Start the app → confirm `init()` then `login()` resolve → the `CometChatConversations` list renders inside `CometChatProvider` (itself inside `CometChatErrorBoundary`) at full size (not a collapsed sliver); open a conversation → the message pane loads and messages send/receive; **clicking "reply in thread" opens the thread panel (default) and its back/close returns to the list** (hidden only if the user opted out), and the thread's MESSAGE LIST reads as a distinct surface matching its own header/composer (not the same shade as the main list — the `--cometchat-message-list-bg` override is scoped on the thread wrapper); **clicking the message-header search icon opens an in-chat search in the side panel scoped to THAT conversation (default), with back to close**; the conversations search bar is wired-or-hidden (no dead-ends); on a narrow viewport it collapses to one pane at a time (list → message → thread/search → back). Blank white screen ⇒ something rendered before `init()` resolved, the Region / env prefix is wrong, or an unbounded render error escaped (add `CometChatErrorBoundary`). A list + message pane with no sizing / no error boundary / dead-ending affordances ⇒ under-delivery (see the golden path). Growing to the full app (tabs + side panel + incoming call) ⇒ verify per `cometchat-react-v7-placement`.

## Explain what you built (REQUIRED close)
After it builds + verifies, don't dump silently — tell the user briefly: **(1) what I wired** (3–5 bullets, NAME the files); **(2) decisions & why**, flagging dev-only AS dev-only (dev **Auth Key** → server auth token for prod; the `<uid>`; OS-follow theme); **(3) what I did NOT touch** (additive — routing/auth/styles intact). Then **(4) offer these THREE options as a SELECTABLE choice and WAIT for the user's pick — do NOT auto-continue:**
- **① Add another feature** → **first check what's ALREADY there, then suggest only the GAP (AUDIT-043).** Read what's wired (the emitted code you built) and ASK which dashboard-gated extensions are already enabled (you can't reliably read per-app dashboard state — don't assume OFF). SUGGEST 3–4 grow-set items that are NEITHER wired NOR already enabled (voice/video **calls** · **search** · **threads** if off · **push** · **AI/smart-replies** · **moderation** · polls/stickers/translation) — **never re-suggest something already on (e.g. translation already enabled in the dashboard)**. **Do NOT suggest `reactions` or `mentions` — they are ON BY DEFAULT in v7 (core messaging; their dashboard extensions are "(Legacy)", already in core — AUDIT-077); if the user asks, say they're already on and offer to customize them.** Then build the chosen one (→ `cometchat-react-v7-features` / `cometchat-react-v7-calls`).
- **② Customize theming** → ask whether they already have a **preset / brand theme** (a brand color, light/dark, or match an existing design system) or want to talk through the options, then wire it (→ `cometchat-react-v7-customization`).
- **③ Test it manually** → do NOTHING further — hand it back so the user runs and checks it themselves.

A PARKED capability (push · migration · SDK-only) → isn't in this pack yet: say so honestly + link CometChat's docs. **This 3-option close runs after EVERY implementation (`RULES.md` §19 / AUDIT-040).**
