---
name: cometchat-react-v7-calls
description: "Add voice & video calling to a React app with the CometChat v7 UI Kit — install the Calls SDK, enable calling on the UIKit settings, mount the incoming-call surface, and wire 1:1 ring / group join. Bakes the real gotchas (ms idle-timeout, zero-dimension call surface, Next.js SSR, no group-ring, HTTPS/getUserMedia). Triggers: 'add voice and video calls', 'add calling to my chat', 'enable video call', 'add call buttons', 'show call logs', 'cometchat calling react'."
license: "MIT"
compatibility: "React >=18 <21; @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0); @cometchat/chat-sdk-javascript ^4.1.9; @cometchat/calls-sdk-javascript ^5 (5.0.0 — separate, NOT bundled)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react calls voice video calling webrtc v7 uikit"
---

> **Ground truth:** calling is part of `@cometchat/chat-uikit-react@7` (the call UI ships INSIDE the kit — there is no separate calls-UI package), but the WebRTC engine is a SEPARATE, NOT-bundled dependency: `@cometchat/chat-uikit-react@^7` + `@cometchat/chat-sdk-javascript@^4.1.9` + **`@cometchat/calls-sdk-javascript@^5`** (major 5 — distinct from the chat SDK's v4). Every `CometChat*` symbol below exists in the `web-v7` catalog. Exhaustive props + advanced call surfaces are FETCHED from the docs `.md` twins via `cometchat-react-v7-core/references/docs-map.md`. **APPEND to the user's app — additive wiring only** (`RULES.md`).

## Companion skills (read first)
- `cometchat-react-v7-core` — install, credentials, `init→login→render`, `CometChatProvider`. This skill ASSUMES it (calling is enabled on the SAME init).
- `cometchat-react-v7-components` — the component catalog (message header the call buttons live in).
- `cometchat-react-v7-features` — `voice-video-calls` is the feature entry; this skill is its operational depth.

## Use this skill when
"add voice & video calls", "add calling to my chat", "enable video call", "add call buttons", "show call logs". Precondition: chat is already integrated (core done) — calling rides on the same init/login.

## Prerequisites & install
Core setup done (init + login + `CometChatProvider`). Calling adds ONE package:
```bash
npm install @cometchat/calls-sdk-javascript@5
```
> The Calls SDK is **major 5** (not the chat SDK's v4) and is **NOT bundled** by the UI Kit — if it isn't installed, every call affordance stays hidden. Do not "upgrade" `@cometchat/chat-sdk-javascript` to a non-existent v7; it stays `^4.1.9`.

## Enable calling (BAKED — the two-part contract, the #1 gotcha)
Calling is OFF until BOTH are true: the Calls SDK is installed (above) **and** calling is turned ON in the init settings. Since the core inits via **`CometChatUIKit.initFromSettings`** (telemetry — `RULES.md` §5 / AUDIT-084), enable calling IN the SAME settings object with a truthy **`uiKit.callsSDK`**:
```tsx
import { CometChatUIKit } from "@cometchat/chat-uikit-react";

await CometChatUIKit.initFromSettings({
  appId: APP_ID, region: REGION,
  credentials: { authKey: AUTH_KEY },                        // dev-only; prod → server-minted auth token
  chatSDK: { presenceSubscription: { type: "ALL_USERS" } },
  uiKit: { callsSDK: {} },   // ← turns calling ON (the initFromSettings equivalent of setCallingEnabled(true))
});
```
> **How calling maps in the initFromSettings path (verified vs the compiled 7.1.x kit; DOCS-GAP).** The kit computes `callingEnabled = !!settings.uiKit.callsSDK`, so a **truthy `uiKit.callsSDK`** is the `initFromSettings` equivalent of `UIKitSettingsBuilder().setCallingEnabled(true)` — WITHOUT it, call buttons + incoming-call render nothing. The docs don't yet document this shape (owner: **docs** — confirm with a live call). The classic path still works — `CometChatUIKit.init(new UIKitSettingsBuilder()…setCallingEnabled(true).build())` — but it SKIPS the ai-agent telemetry attribution, so prefer `initFromSettings`.
> No separate `CometChatUIKitCalls.init()` is needed for the default path. (`CometChatUIKitCalls` is the kit's namespace for advanced call-settings builders; reach for it only on a custom surface — FETCH then.) `initFromSettings` routes the Calls SDK internally — do NOT call raw `CometChat.init()`.

## Wire the UI (BAKED — least-code path)
Two moves cover ringing end-to-end:
1. **Mount `CometChatIncomingCall` ONCE at the app root** (above your routes). It self-manages visibility — renders nothing when idle, rings on an inbound call — so **no conditional wrapper**. It attaches its own SDK listeners.
   ```tsx
   import { CometChatIncomingCall } from "@cometchat/chat-uikit-react";
   // at the app shell, inside CometChatProvider, above the router:
   <CometChatIncomingCall />
   ```
2. **Let `CometChatMessageHeader` surface the call buttons.** When a `user`/`group` is selected, the header composes voice/video call buttons itself once calling is enabled — you usually mount NOTHING extra. Only drop a standalone `CometChatCallButtons user={user}` (1:1) or `group={group}` on a CUSTOM header that has no `CometChatMessageHeader`. **Never mount both** — a standalone `CometChatCallButtons` next to a `CometChatMessageHeader` duplicates the buttons.

**Call logs** (optional history surface): `CometChatCallLogs` on a sidebar or a `/calls` route (`onItemClick`, `onCallButtonClicked`, `callLogRequestBuilder`). It does NOT auto-refresh on a new call — remount to refresh. **It shows the kit's "OOPS! …" screen when call logs aren't available — and, verified live, it renders that from its OWN INTERNAL error state WITHOUT throwing, so a host `CometChatErrorBoundary`/`fallbackView` CANNOT override it and `onError` may not fire. A fallbackView is NOT the fix (AUDIT-162).** **Enabling calling is NOT sufficient for `CometChatCallLogs`:** call-logs availability is a SEPARATE plan/capability gate — an app can have calling ON (Voice/Video buttons render) yet `CometChatCallLogs` still "OOPS" because call-logs isn't in the plan. **The only reliable protection is to GATE the Calls tab on real call-logs AVAILABILITY** (a one-time SDK probe you own — `new CometChatCalls.CallLogRequestBuilder().setLimit(1).setAuthToken(await CometChatUIKitCalls.generateToken(...)).build().fetchNext()`, show the tab only on success — or your known plan), NOT merely on calling being enabled; default the tab OFF so a plain app never dead-ends. **Import discipline (AUDIT-204): `CallLogRequestBuilder` is NOT a named export of `@cometchat/calls-sdk-javascript` — it is a STATIC on the `CometChatCalls` default-export class** (verified vs calls-sdk 5.0.5 `dist/index.d.ts`): use `import { CometChatCalls } from "@cometchat/calls-sdk-javascript"; new CometChatCalls.CallLogRequestBuilder()…` — a `import { CallLogRequestBuilder } from "@cometchat/calls-sdk-javascript"` FAILS (TS2614). `generateToken` is on `CometChatUIKitCalls` (from `@cometchat/chat-uikit-react`). (Gated Calls-tab recipe with the full probe + imports: `../cometchat-react-v7-placement/references/recipes.md` Combined-app recipe.)

### 1:1 rings, groups JOIN (BAKED — no group-ring)
- **1:1:** call buttons → the kit initiates a call → the recipient's root `CometChatIncomingCall` RINGS → accept → the ongoing-call surface. The kit drives outgoing → ongoing for you.
- **Group:** call buttons on a group send a **group-call meeting message** into the chat; members **JOIN** from that message. There is **no "ring the whole group" primitive** — surface the join affordance, never wait for a ring.

## Custom call surfaces (FETCH — don't bake)
For anything past the default ring/join — a custom ongoing-call screen (`CometChatOngoingCall`), a bespoke call manager (`CometChatOutgoingCall`), idle-timeout tuning, screen-share, picture-in-picture, device selection, recording, virtual background — FETCH the exact props/API from the docs `.md` twins via `cometchat-react-v7-core/references/docs-map.md` (rows: `call-buttons` · `incoming-call` · `outgoing-call` · `call-logs` · `calls-setup` · `calls-react-integration` · the per-feature Calls-SDK pages). These props change; never emit them from memory or read `.d.ts`.

## Common pitfalls (BAKED — these bite in production)
- **Idle-timeout is in MILLISECONDS.** `180` = 180 ms, so the "are you still there?" prompt fires and exits instantly. Use `180_000` for 3 minutes. (Exact v7 field/clamp → FETCH the idle-timeout page.)
- **Zero-dimension call surface = crash/blank.** A custom ongoing-call container with 0 width/height throws or renders nothing (e.g. `h-full` on an auto-height flex parent). Give the call surface a content-INDEPENDENT height + width per the reflow-free-surface standard (`../cometchat-react-v7-core/references/layout.md`) — a pinned flex chain with `min-height:0`, or a `100dvw/100dvh` overlay. Same class of bug as the chat-collapse/reflow issue: the kit call UI fills its parent, so a content-driven box collapses or grows-into-place.
- **`Container dimensions and number of tiles must be positive` on leave (non-fatal).** Even the kit's DEFAULT ongoing-call dialog logs this error from a Jitsi `ResizeObserver` as the dialog collapses to 0×0 while unmounting on "Leave session". It's a Calls-SDK teardown race — **non-fatal: the app recovers to the chat surface** — but it's an uncaught console error every hang-up, so a strict "no console errors" gate must allowlist/filter it. Owner: uikit/calls-sdk (not a host bug). Don't try to "fix" it host-side.
- **HTTPS required.** `getUserMedia` (camera/mic) only works on `localhost` or HTTPS — calling silently no-ops on a plain-HTTP non-localhost origin.
- **Next.js SSR.** Render CometChat (and especially the calls SDK) client-only: `"use client"` + `dynamic(() => import(...), { ssr: false })`. If the build then fails with `Can't resolve 'fs'` / `'path'`, add a webpack fallback (`config.resolve.fallback = { fs: false, path: false }`) — a Calls-SDK-v5 bundling quirk. See `cometchat-react-v7-core/references/ssr.md`.
- **Cleanup on custom surfaces.** On a hand-rolled ongoing-call screen, end the session and stop the tracks (`stream.getTracks().forEach(t => t.stop())`) on hangup/unmount or the camera light stays on. The kit-driven `CometChatIncomingCall`/ongoing flow handles this for you — prefer it.
- **Screen-share / PiP / device-select / recording / virtual-background are NOT on by default** — each is separate wiring on its own Calls-SDK page. Don't claim the default screen includes them.

## Verify it works
Calling is enabled (SDK installed + `uiKit:{callsSDK:{}}` on `initFromSettings` — the `initFromSettings` equivalent of the classic `setCallingEnabled(true)`); a 1:1 call from the header buttons RINGS the other user's root `CometChatIncomingCall`; accept connects audio+video in a non-collapsed surface; a group call posts a join message (no ring); hang-up releases the camera/mic (light off). If call buttons never appear: the SDK isn't installed or calling isn't enabled. If the call screen is blank: the container is zero-dimension or the origin isn't HTTPS.

**Close (after it builds):** end with the shared 3-option selectable menu and WAIT for the pick — **① add another feature** (suggest a few not-yet-wired) · **② customize theming** · **③ test it manually** (stop; let the user check). Same contract as the `cometchat-react-v7-core` close (`RULES.md` §19).
