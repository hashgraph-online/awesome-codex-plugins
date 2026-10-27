---
name: cometchat-angular-v5-calls
description: "Add voice and video calling to an Angular CometChat app — install the calls SDK, mount the incoming-call listener at app root, call buttons in the message header, and call logs. Triggers: 'add voice calling', 'add video calls', 'enable calling', 'show call history', 'incoming call not ringing'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified) + @cometchat/calls-sdk-javascript ^5.0.3; Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular calls v5 voice video calling webrtc call-logs"
---

> **Ground truth:** calling UI ships INSIDE `@cometchat/chat-uikit-angular@5` — there is no separate calls-UI package — but the WebRTC engine is a SEPARATE, NOT-bundled peer: `@cometchat/calls-sdk-javascript@^5.0.3` (major 5, distinct from the chat SDK's v4). Every `CometChat*` symbol below exists in the `angular-v5` catalog. Exhaustive inputs/outputs and advanced call surfaces are FETCHED, not baked — `{DOCS_BASE}/ui-kit/angular/call-features.md`, the per-component pages (`/components/cometchat-incoming-call`, `-call-buttons`, `-call-logs`, `-outgoing-call`), and `/guides/call-log-details`; base + paths in `cometchat-angular-v5-core/references/docs-map.md`. **APPEND to the user's app — additive wiring only** (`RULES.md`).

## Companion skills (read first)
- `cometchat-angular-v5-core` — install, credentials, `init→login→render`. Assumed.
- `cometchat-angular-v5-placement` — where the incoming-call listener mounts.

## Use this skill when
Adding voice/video calling, or diagnosing calls that never ring.

## Prerequisites & install — calls needs a second package
```bash
npm install @cometchat/calls-sdk-javascript@^5
```
It is an **optional peer** of the UI Kit (`^5.0.3`), so it is not installed by default. Without it the call components are inert and `CometChatUIKit.isCallingEnabled()` returns false.

Calling must also be enabled for the app in the dashboard. Code alone is not enough.

## ⚠️ Installing the package is NOT what turns calling on
`core` inits with `initFromSettings`, and on that path the kit derives calling from the settings object:

```ts
// verified in the shipped 5.1.0 bundle
const callingEnabled = !!settings.uiKit?.['callsSDK'];
if (callingEnabled) builder.setCallingEnabled(true);
```

So you must declare a **`uiKit.callsSDK` block** or calling stays off no matter what you installed:

```ts
CometChatUIKit.initFromSettings({
  appId, region,
  credentials: { authKey },
  chatSDK: { presenceSubscription: { type: 'ALL_USERS' } },
  uiKit: { callsSDK: {} },          // ← REQUIRED for calling on the initFromSettings path
});
```

**Symptom if you miss it:** `<cometchat-call-buttons>` renders as a **zero-size empty element** and the message header shows no call buttons. Nothing errors, nothing logs, and the package is installed — so it reads as a layout or CSS bug. `CometChatUIKit.isCallingEnabled()` returns `false`; check that first.

> The docs' builder path uses `.setCallingEnabled(true)` on `UIKitSettingsBuilder` instead. Both are correct for their own init — see `cometchat-angular-v5-core/references/lifecycle.md`. Do not mix them.

## The four things, in order
1. **Install the calls SDK** (above).
2. **Mount `<cometchat-incoming-call>` at APP ROOT** — not in the chat page.
3. **Add call buttons** — the message header renders them by default.
4. **Optionally add call logs.**

Step 2 is the one that goes wrong.

## Incoming calls — app root, not the chat route
```html
<!-- app.component.html -->
<cometchat-incoming-call
  (callAccepted)="onAccepted($event)"
  (callDeclined)="onDeclined($event)"
  (error)="onError($event)">
</cometchat-incoming-call>
<router-outlet></router-outlet>
```
Mounted inside the chat page it unmounts the moment the user navigates elsewhere, so calls stop ringing anywhere except that one route. It looks like the calls SDK is broken; it is a placement bug.

Remember `CometChatIncomingCallComponent` in the root component's `imports: []`.

## Call buttons
`<cometchat-message-header>` renders voice and video buttons itself — **check the running app before adding your own.** Suppress with `[hideVoiceCallButton]="true"` / `[hideVideoCallButton]="true"`.

The default is not hardcoded: the header reads `COMETCHAT_GLOBAL_CONFIG` and tracks whether you set the input explicitly, so an app-wide config can hide the buttons even though nothing on the component says so. If they are missing, check the global config before concluding the header does not render them — and if they are present, do not add `<cometchat-call-buttons>` alongside or you get two sets.

Standalone, elsewhere in your UI:
```html
<cometchat-call-buttons [user]="activeUser()" [group]="activeGroup()" (error)="onError($event)"></cometchat-call-buttons>
```

Both call components must be in the consuming component's `imports: []` — omitted, they
render nothing and never ring. Mount `<cometchat-incoming-call>` at the **app root**, not
inside a route, or it stops ringing the moment the user navigates away:

```ts
import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ChatStateService,
  CometChatCallButtonsComponent,
  CometChatIncomingCallComponent,
  CometChatUIKitCalls,
} from '@cometchat/chat-uikit-angular';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, CometChatCallButtonsComponent, CometChatIncomingCallComponent],
  template: `
    <cometchat-incoming-call (callAccepted)="onAccepted($event)"></cometchat-incoming-call>
    <cometchat-call-buttons [user]="activeUser()" [group]="activeGroup()"></cometchat-call-buttons>
  `,
})
export class AppRootComponent {
  private readonly chatState = inject(ChatStateService);
  readonly activeUser = computed(() => this.chatState.activeUser() ?? undefined);
  readonly activeGroup = computed(() => this.chatState.activeGroup() ?? undefined);
  // CometChatUIKitCalls is the calls-SDK accessor the kit exposes; it is null until the
  // SDK has loaded, so never touch it during construction.
  readonly calls = CometChatUIKitCalls;
  onAccepted(_call: unknown) { /* route to your ongoing-call screen */ }
}
```

## Ongoing and outgoing
The kit drives these once a call is accepted. Outputs, if you need to react:

| Component | Outputs |
| --- | --- |
| `<cometchat-incoming-call>` | `callAccepted` `callDeclined` `error` |
| `<cometchat-outgoing-call>` | `callCanceled` `error` |
| `<cometchat-ongoing-call>` | `callEnded` `error` |
| `<cometchat-call-buttons>` | `error` |
| `<cometchat-call-logs>` | `itemClick` `callButtonClicked` |
| `<cometchat-call-bubble>` | `buttonClick` |

`<cometchat-ongoing-call>` takes `[sessionID]` and optionally `[callSettingsBuilder]` / `[isAudioOnly]`. Do not build your own call screen — WebRTC state, permissions and teardown are handled.

## Call history
> ⚠️ **`<cometchat-call-logs>` HARD-CRASHES if it mounts before the Calls SDK has loaded.**
> Its `ngOnInit` synchronously runs `new CometChatUIKitCalls.CallLogRequestBuilder()`, but
> `CometChatUIKitCalls` is `null` until the lazily-loaded Calls SDK resolves — so on a fresh
> `initFromSettings` app the tab renders an **"OOPS! / Retry"** error state and logs
> `[CometChatCallLogs] Error: TypeError: Cannot read properties of null (reading 'CallLogRequestBuilder')`.
> **Retry does NOT recover it.** This is the same "`CometChatUIKitCalls` is null until the SDK
> has loaded, so never touch it during construction" trap as the standalone accessor above — it
> just bites INSIDE the kit's own component. **GATE the call-logs surface on the calls-SDK namespace
> ACTUALLY being populated — not on `callingReady` alone.** Verified live (AUDIT-163):
> `CometChatUIKit.callingReady` defaults to a **pre-resolved** `Promise.resolve()`, and even after
> `initCalling()` runs the lazily-loaded `CometChatUIKitCalls` namespace can still be `null` (e.g. the
> calls chunk never loaded) — so a `callingReady`-ONLY gate STILL crashes. Await `callingReady`, THEN
> confirm `CometChatUIKitCalls` is non-null before mounting:
```ts
// component
import { CometChatUIKit, CometChatUIKitCalls } from '@cometchat/chat-uikit-angular';
readonly callsReady = signal(false);
constructor() {
  CometChatUIKit.callingReady
    .then(() => this.callsReady.set(!!CometChatUIKitCalls))   // namespace must be populated, not just "ready"
    .catch(() => this.callsReady.set(false));
}
```
```html
<!-- Do NOT mount <cometchat-call-logs> unguarded — it NPEs on CometChatUIKitCalls being null. -->
<cometchat-call-logs *ngIf="callsReady()" (itemClick)="openCall($event)"></cometchat-call-logs>
<div *ngIf="!callsReady()">Loading call history…</div>
```
> **STOPGAP** (remove once the kit component awaits `getCometChatCalls()` / null-guards
> `CometChatUIKitCalls` itself — filed as a UIKit bug; the docs page also omits this prerequisite —
> DOCS-BACKLOG). `isCallingEnabled()` is the sync settings check; **`callingReady` + a `CometChatUIKitCalls`
> null-check** is what actually guards the mount (`callingReady` alone is NOT enough — proven live).

Also available: `CallLogsService` for headless querying, and `guides/call-log-details` for a detail view.

## Environment requirements
- **HTTPS or localhost.** `getUserMedia` is blocked on plain HTTP, so calls fail on a LAN IP over http.
- Microphone/camera permission is a **user-gesture** prompt — trigger it from a click, never on load.
- `CometChatUIKit.callingReady` is a promise that resolves once calling is initialised; `isCallingEnabled()` is the synchronous check.

## Common pitfalls
1. **Listener in the chat page** → calls ring only on that route.
2. **`uiKit.callsSDK` missing from `initFromSettings`** → calling silently off; call buttons render as zero-size empty elements. Installing the package is not enough.
3. **Calls SDK not installed** → components inert, no error.
4. **Calling not enabled in the dashboard** → code correct, nothing happens.
5. **Plain HTTP** → `getUserMedia` blocked.
6. **Duplicate call buttons** → the header already renders them.
7. **Hand-rolled call screen** → loses WebRTC teardown; use `<cometchat-ongoing-call>`.
8. **No zero-height container** — the ongoing-call surface needs real dimensions like any other component.

## Verify it works
Two browsers, two users, HTTPS or localhost · caller sees outgoing UI, callee's device rings **from any route** · accepting connects audio/video both ways · ending returns both to chat · the call appears in call logs · no console errors.

## Explain what you built (REQUIRED close)
Tell the developer what changed, naming the files: calling — the packages added, that `uiKit: { callsSDK: {} }` is what switches it on, and where `<cometchat-incoming-call>` is mounted. Flag anything dev-only as dev-only, and say what you did **not** touch — this is additive.

**Then offer these THREE options as a SELECTABLE choice and WAIT for the pick — never auto-continue (`RULES.md` §19):**
1. **Add another feature** → call-log details, or another grow-set feature from `features.angular-v5.json`. **Never offer an `auto` entry** (reactions, mentions, receipts, typing, media) — those are core in v5 and already on.
2. **Customize theming** → `cometchat-angular-v5-customization`.
3. **Test it manually** → do nothing further; hand back so the user runs it.
