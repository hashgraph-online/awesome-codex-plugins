---
name: cometchat-js-v5-sdk
description: "Add voice & video calling to any web app FROM SCRATCH with the headless CometChat Calls SDK v5 (`@cometchat/calls-sdk-javascript@5`) — no prebuilt UI Kit. init→login→generateToken→joinSession, event listeners, in-call actions (mute/video/screen-share/record/layout), meet-style session rooms AND 1:1 ringing (Chat SDK signaling + Calls SDK media). Triggers: 'add calling from scratch', 'standalone video call', 'headless calls sdk', 'build my own call UI', 'meeting room join by session id', 'one-on-one ringing call without uikit'."
license: "MIT"
compatibility: "Modern WebRTC browser (Chrome 72+/Firefox 68+/Safari 12.1+/Edge 79+); HTTPS (or localhost) for getUserMedia; @cometchat/calls-sdk-javascript@^5 (5.0.5). 1:1 ringing also needs @cometchat/chat-sdk-javascript@^4 for signaling. Framework-agnostic (vanilla JS core; React/Vue/Angular/Next recipes)."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat calls sdk v5 headless voice video webrtc javascript calling standalone"
---

> **Ground truth:** `@cometchat/calls-sdk-javascript@5` + catalog `web-calls-v5.json` (the closed symbol list — every `CometChatCalls.*` below exists in it). Official docs: `/calls/javascript/**` = **v5** · Docs MCP. Fetch exact `SessionSettings` fields, event names, and action-method signatures from the docs (`references/docs-map.md`) — never memory. **APPEND to the user's app — additive wiring only** (`RULES.md`). This is the HEADLESS path (no UI Kit); for the prebuilt drop-in call UI use `cometchat-react-v7-calls` instead.

## Companion skills (read first)
- **Standalone/headless entry** — this skill owns its own package (the Calls SDK) and has no `-core` sibling; it is self-contained for meet-style calling.
- **For 1:1 RINGING only** it also drives the **Chat SDK** (`@cometchat/chat-sdk-javascript@4`) for call signaling — signatures fetched from docs via `references/docs-map.md` (§ "1:1 RINGING"). It does NOT depend on the React UI Kit.
- **Prefer the UI Kit instead?** If the app also wants chat and a prebuilt call UI, use `cometchat-react-v7-core` + `cometchat-react-v7-calls` — not this skill.

## Use this skill when
"add calling from scratch / without the UI Kit", "standalone voice/video", "build my own call screen", "headless calls SDK", "meeting-room join by session id", "one-on-one ringing call". Precondition: the caller chose the **from-scratch / standalone** path (the "add calling" router asks this). If they want the prebuilt call UI, route to `cometchat-react-v7-calls`.

## Prerequisites & install
```bash
npm install @cometchat/calls-sdk-javascript@5
```
- **1:1 ringing** additionally needs the Chat SDK for signaling:
  ```bash
  npm install @cometchat/chat-sdk-javascript@4
  ```
- Credentials/env: App ID · Region · Auth Key (dev only). To fetch from the dashboard, load the CLI on demand — `npx @cometchat/skills-cli@3 auth login` → `provision use --app-id <id> --json` (writes `.cometchat/config.json`; `@3` pins the CLI major that matches the v5 skills). Or paste manually from Dashboard → Credentials. Mint **auth tokens server-side** for production; never ship the Auth Key. HTTPS (or `localhost`) is required for camera/mic (`getUserMedia`).

## Init & login ordering (BAKED — invariant)
`CometChatCalls.init(...)` (once, resolve first) → `CometChatCalls.login(uid, authKey)` **or** `loginWithAuthToken(token)` → then `generateToken` / `joinSession` / listeners. Nothing renders/joins before init+login resolve.
- **DEFAULT to `CometChatCalls.initFromSettings(settings)`** — the ai-agent / telemetry-attributed path (persists `integrationSource="ai-agent"`), parallel to how the chat core inits via `CometChatUIKit.initFromSettings` / `CometChat.initFromSettings` (RULES §5). It is **INTENTIONALLY undocumented** — ai-agent-only (`@nodoc`, same posture as `CometChatUIKit.initFromSettings` — DOCS-BACKLOG F4/C1) — so the settings-object shape is **baked in `references/docs-map.md`**; pass it **INLINE** (no physical `cometchat-settings.json` file required), never fetched from `/calls/javascript/setup`. The publicly-documented **`CometChatCalls.init({ appId, region })` is the FALLBACK only** (a non-skills / doc-following context).
- Coexisting with the Chat SDK / UI Kit? Their `login()` can re-init the Calls SDK with only appId/region and wipe custom hosts — re-run your calls init after their login, before `CometChatCalls.login`.

## Two build modes (BAKED — the router picks one)
- **Meet-style (session room)** — Calls SDK ONLY. Everyone who joins the same `sessionId` lands in the same call: `generateToken(sessionId)` → `joinSession(token, sessionSettings, containerEl)`. No ringing. This is the `/calls/javascript/react-integration` flow.
- **1:1 ringing** — Chat SDK signals, Calls SDK carries media: `CometChat.initiateCall` → peer `CallListener.onIncomingCallReceived` → `acceptCall`/`rejectCall` → `CometChatCalls.generateToken(call.getSessionId())` → `joinSession(...)`. Fetch Chat-SDK signatures via `references/docs-map.md` § "1:1 RINGING".

## SDK method map (BAKED closed list — from the catalog; signatures → FETCH from docs)
- **Lifecycle:** `CometChatCalls.init` · `CometChatCalls.initFromSettings` · `CometChatCalls.login` · `CometChatCalls.loginWithAuthToken` · `CometChatCalls.logout` · `CometChatCalls.getLoggedInUser` · `CometChatCalls.isUserLoggedIn`
- **Session:** `CometChatCalls.generateToken` · `CometChatCalls.joinSession` · `CometChatCalls.leaveSession` (`startSession` is **deprecated** → use `joinSession`)
- **Events:** `CometChatCalls.addEventListener(eventName, cb, { signal? }) → unsubscribe()` (event names: FETCH the full list from `/calls/javascript/events`)
- **In-call actions** — ⚠️ **for CUSTOM controls ONLY; the default `joinSession` UI already renders all of these** (see the first pitfall). Only reach for them when the user EXPLICITLY asks to replace the built-in controls: `muteAudio`/`unmuteAudio`/`toggleAudio` · `pauseVideo`/`resumeVideo`/`toggleVideo` · `setLayout` · `startRecording`/`stopRecording` · `startScreenSharing`/`stopScreenSharing` · `raiseHand`/`lowerHand` · `switchCamera` · `pinParticipant`/`unpinParticipant` · `showParticipantList`/`hideParticipantList`
- **Devices:** `getAudioInputDevices` · `getAudioOutputDevices` · `getVideoInputDevices` · `getCurrent*Device`
- **Call logs:** `CometChatCalls.CallLogRequestBuilder` → `fetchNext()` (paginated; shape → docs)
- **Constants:** `CometChatCalls.constants.LAYOUT` (`TILE`/`SIDEBAR`/`SPOTLIGHT`) · `.TYPE` (`VOICE`/`VIDEO`) · `.CAMERA_FACING`
> This map is a **curated highlight, NOT the full surface** — the AUTHORITATIVE closed list is the **`web-calls-v5.json` catalog** (83 symbols; it also carries `toggleHand`/`toggleParticipantList`/`endSessionForAll`/`muteParticipant`/`pauseParticipantVideo`/`setChatButtonUnreadCount`/`switchToVideoCall`, device setters (`setAudioInputDevice`…), the virtual-background methods, `startStreaming`/`stopStreaming` (**RTMP live-streaming** — with `streamUrl`/`streamKey`/`hideStreamingButton` in `SessionSettings`; neither the SKILL map above nor the `/calls/javascript/actions` doc foregrounds it, but it is real), `startTranscription`/`stopTranscription` (v5.0.5 — see `/calls/javascript/transcription`), and `TranscriptRequestBuilder`, among others). A symbol is real **iff it's in the catalog** — confirm THERE (not just this map), then fetch its exact signature/params from the docs page in `references/docs-map.md`.

## Listener lifecycle (BAKED)
`addEventListener` RETURNS an unsubscribe function — collect them and call every one on teardown (React: in the effect cleanup), and `CometChatCalls.leaveSession()` on unmount. Register listeners BEFORE `joinSession`. Never leak. You can also pass an `AbortSignal` via the `{ signal }` option for bulk teardown.

## Least-code recipe (meet-style, framework-agnostic)
```ts
// STRICT-TS-CLEAN: type the settings with the EXPORTED SessionSettings, narrow region.
import { CometChatCalls } from "@cometchat/calls-sdk-javascript";
import type { SessionSettings } from "@cometchat/calls-sdk-javascript"; // exported; SessionType/Layout are NOT

1. await CometChatCalls.initFromSettings({ appId, region: region as "us"|"eu"|"in", credentials: { authKey: AUTH_KEY }, callsSDK: {}, chatSDK: {}, uiKit: {} }) // ai-agent telemetry default (integrationSource="ai-agent"); init({appId,region}) is the public-doc fallback
2. await CometChatCalls.login(uid, AUTH_KEY)               // or loginWithAuthToken(token)
3. const { token } = await CometChatCalls.generateToken(sessionId)
4. const unsub = CometChatCalls.addEventListener("onSessionLeft", () => cleanup())
5. const callSettings: SessionSettings = { sessionType: "VIDEO", layout: "TILE" } // annotate → literals narrow
   await CometChatCalls.joinSession(token, callSettings, containerEl)
6. // NO control buttons needed — joinSession's UI ALREADY renders mute/video/screen-share/raise-hand/leave.
7. // teardown → unsub(); CometChatCalls.leaveSession()
```
The `containerEl` MUST have real dimensions — the SDK renders its call surface into it. Fetch the full `SessionSettings` field list from `/calls/javascript/session-settings`. (In plain JS drop the annotations; the doc pages show that JS form.)

## Framework notes (same SDK, per-framework glue)
The recipe above is framework-agnostic; the only per-framework part is WHERE you register listeners / mount the container / tear down. Verified live on React and Angular.
- **React:** provider or component — init via `CometChatCalls.initFromSettings(...)` (the telemetry-attributed default — `integrationSource="ai-agent"`; `init({appId,region})` is the public-doc fallback), then register listeners + `joinSession` in a `useEffect`; teardown in the effect cleanup (call every unsubscribe + `leaveSession`). Recipe: `/calls/javascript/react-integration`.
- **Angular:** a **DI service** wrapping `CometChatCalls` (init via `CometChatCalls.initFromSettings(...)` — the telemetry-attributed default (`integrationSource="ai-agent"`; `init({appId,region})` is the public-doc fallback) → login, `generateToken`, typed `joinSession`, `leaveSession`; expose readiness via an RxJS `BehaviorSubject`) + a component with a **sized `@ViewChild('callContainer') ElementRef`** container; register listeners BEFORE `joinSession`; teardown in **`ngOnDestroy`** (unsubscribe all + `leaveSession`). Recipe: `/calls/javascript/angular-integration` — but ⚠️ THREE things to override:
  - **(a)** its example wires external Mute/Video/Leave buttons — **IGNORE them** (pitfall #1: `joinSession`'s UI already has the controls);
  - **(b)** it targets legacy `@NgModule`/`app.module.ts` — a modern `ng new` is **standalone** (`bootstrapApplication` + `app.config.ts`, class `App`), so use the standalone variant;
  - **(c) ⚠️ NgZone / change detection (the silent dead-state).** CometChat SDK callbacks — event listeners AND the `login`/`generateToken`/`joinSession` promise resolutions — fire OUTSIDE Angular's zone, so any component state you set inside them **won't trigger change detection** (symptom: readiness/call buttons *silently never enable*, even though the SDK succeeded). Fix: drive the template off your `BehaviorSubject` via the **`async` pipe**, AND/OR wrap state writes in **`this.zone.run(() => …)`** (inject `NgZone`) or call `ChangeDetectorRef.detectChanges()`. Not optional — the app looks broken without it.

## Common pitfalls (BAKED)
- **Don't duplicate the built-in call controls (the #1 mistake).** `joinSession` renders a COMPLETE call UI — mute, camera on/off, screen-share, raise-hand, participant list, layout switch, and the red leave/end button are ALL built into the surface it mounts in `containerEl`. Do **NOT** add your own Mute / Start-video / Share-screen / Leave buttons around the container: they are redundant, duplicate the SDK's own controls, and drift out of sync with the real call state. The `muteAudio`/`pauseVideo`/`leaveSession`/… methods are for CUSTOM controls ONLY — reach for them **just when the user EXPLICITLY asks** to replace the default controls (and hide the built-in ones first via `SessionSettings` — `hideControlPanel` for the whole bar, or per-button flags like `hideToggleAudioButton`/`hideRaiseHandButton`/`hideChatButton`; the canonical recipe is `/calls/javascript/custom-control-panel`, fields on `/calls/javascript/session-settings`). Default = render the call surface and stop.
- **Zero-dimension container** — `joinSession` mounts into `containerEl`; if it has `height:0` the call renders invisibly. Give it explicit size (e.g. `height: 500px` / `100dvh`).
- **HTTP (not HTTPS)** — `getUserMedia` needs a secure context; camera/mic silently fail off `localhost`.
- **Joining before init+login resolve** — `generateToken`/`joinSession` reject; always `await` init then login first.
- **Leaked listeners / no `leaveSession`** — every `addEventListener` unsubscribe must run on teardown; call `leaveSession()` on unmount.
- **`startSession` is deprecated** — use `joinSession`; don't pass the old `CallSettings` builder where a plain `SessionSettings` object is expected.
- **Host wipe on coexisting Chat-SDK login** — re-init the Calls SDK after the Chat SDK/UI Kit logs in (see Init ordering).
- **version_conflict** — the Calls SDK is **major 5**, distinct from the Chat SDK's v4; do not "upgrade" the Chat SDK to a non-existent v7.
- **Assuming a signature** — event names, `SessionSettings` fields, and action params are FETCHED from docs, never guessed.
- **1:1 ringing: `CometChat.Call` used only as a TYPE trips `TS6133`** — in strict TS, importing `CometChat` and referencing `CometChat.Call` in type positions only (never as a value) fails with `'CometChat' is declared but its value is never read`. Import the **concrete type** instead: `import { CometChat } from "@cometchat/chat-sdk-javascript"` for the VALUES you call (`initiateCall`/`acceptCall`/`addCallListener`) and `import type { Call } from "@cometchat/chat-sdk-javascript"` for the type. (Same class as the `SessionSettings`/`CometChatCalls` strict-TS trap.)
- **Strict-TS widening (the doc's bare-object form doesn't compile as-is)** — the doc pages pass `joinSession(token, { sessionType: "VIDEO", layout: "TILE" }, el)` and `init({ appId, region })` as plain JS. In a strict-TS app (the stock Vite `react-ts` template: `strict` + `verbatimModuleSyntax` + `noUnusedLocals`) those literals WIDEN to `string` and fail `tsc` (TS2345 vs `SessionSettings`; TS2322 for `region`). Fix: `import type { SessionSettings }` (it's exported; `SessionType`/`Layout` are NOT) and annotate the settings object — `const s: SessionSettings = {…}` (or `satisfies SessionSettings`) — and narrow `region` to `"us"|"eu"|"in"`.

## Verify it works
- **Tier-1 catalog:** every `CometChatCalls.*` symbol emitted appears in `web-calls-v5.json` (`node test-suite/scripts/verify-catalog.mjs --family web-calls-v5`).
- **Tier-2 fences:** the emit type-checks against the installed `@cometchat/calls-sdk-javascript@5` `.d.ts`.
- **Tier-3b headless smoke:** `node test-suite/scripts/sdk-smoke.mjs --family web-calls-v5 [--live|--dry]` runs init→login→generateToken→(join wiring)→listener-teardown. Media/`joinSession` needs a real WebRTC/DOM context, so the node smoke covers the token+listener round-trip (`--dry` proves wiring without a backend); the actual call render is verified in a browser harness. Flag "dry-mock only, not live-certified" honestly where true.
