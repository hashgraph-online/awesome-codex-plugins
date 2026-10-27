---
name: cometchat-react-v7-troubleshooting
description: "Diagnose a broken CometChat React v7 integration — blank panes, a collapsed/0-height surface, empty lists, no messages, the kit's error state, events that never fire, or a version_conflict. Triggers: 'cometchat react not working', 'chat is blank', 'conversations empty', 'messages not showing react', 'something went wrong cometchat', 'cometchat react errors', 'why is my chat broken'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-react ^7 (7.1.x–7.2.x verified); React 18–19; Vite / Next.js / CRA / React Router / Astro"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react v7 troubleshooting debug diagnostics blank-screen version-conflict"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. Symbols/signatures are verified against `cometchat-react-v7-core` + its catalog and FETCHED via `references/docs-map.md`; the rules referenced (init order, layout sizing, credentials) are `RULES.md`. This diagnostics catalog is cross-checked against the live `{DOCS_BASE}/ui-kit/react/troubleshooting.md` page (base + paths in `cometchat-react-v7-core/references/docs-map.md`), and adds the host-side/runtime symptoms it doesn't cover.

## Companion skills (read first)
- `cometchat-react-v7-core` — the correct init→login→render order, credentials, and the reflow-free layout the fixes below restore.

## Use this skill when
A React CometChat integration compiles but misbehaves at runtime: blank, empty, unresponsive, or throwing.

## Start here — React fails on the ORDER and the BOX
Two causes explain most "it's blank":
1. **A kit component rendered before `init()` + `login()` resolved.** The surface must be gated on the resolved logged-in user. Rendering it eagerly (or during SSR) yields an empty/erroring pane.
2. **The container has no height.** The kit fills its parent; a parent at `height:auto`/`0` collapses it to a sliver. This is a host CSS defect, not a kit bug (`RULES.md` → Layout / sizing).

## Symptom → cause → fix
| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Blank/white, no errors | Surface rendered before init+login resolved | Gate render on the resolved user; keep `CometChatErrorBoundary` for a visible fallback |
| Blank during SSR / `window is not defined` | A kit component imported or rendered on the server (Next.js, Astro, Remix) | Render the surface client-only — `"use client"` + `dynamic(..., { ssr:false })` (Next), `client:only` (Astro); see core `references/ssr.md` |
| Surface ~0px / cramped top-left | Ancestor chain has no height | `html,body,#root{height:100%}` + a pinned surface (`100dvh` full-app) + panes `min-height:0`; see core `references/layout.md` |
| "OOPS! Looks like something went wrong" | The kit's error state — a call threw (often a custom `ConversationsRequestBuilder` with no `.setLimit(n)`, or a bad Region) | Add `.setLimit(30)`; confirm Region matches the dashboard app |
| Conversations empty | New/seeded app has no conversations yet, or scope excludes them | Send a first message; check `conversationsRequestBuilder` scope (`user`/`group`) matches intent |
| `login()` fails "user not found" | UID does not exist in the app | Use a real UID (Dashboard → Users; fresh apps seed `cometchat-uid-1`) — never a guessed `superhero*` |
| Nothing updates live | Missing/duplicated listeners, or StrictMode double-mount | Add listeners with a stable ID, remove on unmount; guard the init/login in-flight (`cometchat-react-v7-patterns`) |
| Roster rows appear TWICE + ~30 "duplicate key" errors (dev only) | React **StrictMode** double-invokes effects; the roster drop-ins `CometChatUsers`/`CometChatGroups`/`CometChatGroupMembers` double-append (kit de-dupe gap; `CometChatConversations` is unaffected) | A dev-only StrictMode artifact — gone in `vite build`/prod. Do **NOT** remove StrictMode to "fix" it; verify the roster in a production build. Kit issue — report upstream |
| Localized keys shown raw (e.g. `group_info`) | Wrong/stale i18n key or provider missing | Use the kit component / correct key; ensure `CometChatProvider` wraps the tree |
| Works in dev, blank in prod | Wrong env prefix → Auth Key/App ID missing in the bundle | Fix the bundler prefix; grep the build (`cometchat-react-v7-production`) |
| `version_conflict` on detect | Project on UI Kit v6 while skills target v7 | STOP and reconcile — migrate v6→v7 (`cometchat-react-v7-migration`), or stay on v6 by installing the older **v4 skills pack** (it targets the v6 UI Kit) |

## When the table does not cover it
Open the browser console + network tab: a `401` is auth (bad token/Auth Key/Region), a `402` is a plan-gated feature (e.g. Search — enable it in the dashboard), a `4xx` "no conversation yet" is benign. Then fetch the feature's page via `cometchat-react-v7-core/references/docs-map.md`. Never diagnose from `node_modules`/`.d.ts` or memory.

## Verify it works
Init+login resolve before the surface renders · the surface has real dimensions (not a sliver) · conversations render or show the kit's empty state (not the error state) · a message sends and arrives live · no raw localization keys · production build carries no Auth Key.

## What NOT to do
Do not silence the error boundary to hide a thrown call; do not hard-code a UID to dodge "user not found"; do not read kit internals to work around a missing prop — fetch the documented prop instead.
