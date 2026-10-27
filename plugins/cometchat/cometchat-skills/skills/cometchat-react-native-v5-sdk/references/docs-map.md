# docs-map — `cometchat-react-native-v5-sdk` (Calls SDK v5, React Native, headless)

**Doc channel — PREFER the MCP, FALL BACK to a fetch** (`RULES.md` §"Canonical doc channel"). When the
CometChat docs MCP is connected, reach every page through it — `fetch_cometchat_doc_page("/calls/react-native/<page>")`
for a known page, `search_cometchat_docs` for a conceptual question. When it is **not** connected, tell the user and help them add it — `claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp` (or reinstall/enable the plugin), then retry — and only if it still will not connect, fetch
`DOCS_BASE` + the path + `.md` instead (below). **Never require the MCP** — an agent with no MCP must still
be able to read every page here. Either way the `<path>` catalog below decides WHICH page; MCP-vs-fetch is
only HOW.

Every path below is **v5**. Do not read `node_modules` or `.d.ts` for signatures — the catalog
(`rn-calls-v5.json`) says what EXISTS; these pages say what it takes.

## DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)

```
DOCS_BASE = https://www.cometchat.com/docs
```

> Production docs (`https://www.cometchat.com/docs`). **Fetch rule:** `DOCS_BASE` + the path shown + `.md` → raw
> Markdown, with the code fences and prop tables intact.
>
> Example: `{DOCS_BASE}/calls/react-native/join-session.md`
>
> Full page index if you need to discover a page not listed below: `{DOCS_BASE}/llms.txt`

> ⚠️ **Never `search("default calling")` or `search("react native calling")` to find the ringing flow.** Search surfaces the STALE `/calls/v4/react-native/**` tree (deprecated `startSession`, `CallSettingsBuilder`, no v5 event set). Go DIRECTLY to the paths below.

## Path catalog

| Topic | Path | Fetch it for |
|---|---|---|
| Overview / architecture | `/calls/react-native/overview` | the call flow diagram, the single-active-session rules, the feature index |
| Setup | `/calls/react-native/setup` | the 6 pinned peer deps, iOS `Info.plist` + Background Modes, Android manifest + runtime permissions, New Architecture note |
| Authentication | `/calls/react-native/authentication` | `init` / `login` / `loginWithAuthToken` signatures and the auth-token story |
| **Join session** | `/calls/react-native/join-session` | `generateToken(sessionId)`, `<CometChatCalls.Component callToken sessionSettings />` props, error codes |
| Session settings | `/calls/react-native/session-settings` | the FULL `sessionSettings` field list (all `hide*` flags, `audioMode`, `idleTimeoutPeriodBeforePrompt`, `enableIOSPictureInPicture`) |
| Actions | `/calls/react-native/actions` | exact params for `muteAudio`/`setLayout`/`switchCamera`/… |
| Events | `/calls/react-native/events` | the AUTHORITATIVE event-name list for `addEventListener` |
| **Ringing (1:1)** | `/calls/react-native/ringing` | the Chat-SDK signaling half — see § 1:1 RINGING below |
| Call layouts | `/calls/react-native/call-layouts` | `TILE` / `SIDEBAR` / `SPOTLIGHT` behaviour |
| Audio modes | `/calls/react-native/audio-modes` | `setAudioMode` + `AUDIO_MODE` values (RN-only) |
| Recording | `/calls/react-native/recording` | dashboard gating, `autoStartRecording`, recording events |
| Call logs | `/calls/react-native/call-logs` | history read = **Calls SDK** `new CometChatCalls.CallLogRequestBuilder()` (there is NO `CometChat.CallLogRequestBuilder` on the Chat SDK); add `.setHasTranscriptions(true)` for the transcript opt-in. `CometChatCalls.CallLog` shape. |
| Participant management | `/calls/react-native/participant-management` | moderator actions, `endSessionForAll` vs `leaveSession` |
| Screen sharing | `/calls/react-native/screen-sharing` | **receive-only on RN** — confirm before emitting any control |
| Picture-in-picture | `/calls/react-native/picture-in-picture` | in-app tile vs iOS system PiP |
| Raise hand | `/calls/react-native/raise-hand` | `raiseHand`/`lowerHand`/`toggleHand` |
| Idle timeout | `/calls/react-native/idle-timeout` | `idleTimeoutPeriodBeforePrompt` |
| **VoIP / background ringing** | `/calls/react-native/voip-calling` | CallKit+PushKit (iOS), ConnectionService (Android), `registerTokenForPushNotification` — see § BACKGROUND RINGING |
| Background handling | `/calls/react-native/background-handling` | keeping an ACTIVE call alive when the app backgrounds (distinct from ringing a closed app) |
| Migration v4→v5 | `/calls/react-native/migration-guide-v5` | the deprecated-vs-current mapping; read it when touching legacy code |

## BAKED — `initFromSettings` (intentionally undocumented)

`CometChatCalls.initFromSettings(settings)` is the **ai-agent / telemetry-attributed** init and the DEFAULT for this skill (persists `integrationSource="ai-agent"`). It is deliberately `@nodoc` — ai-agent-only, the same posture as `CometChatUIKit.initFromSettings` (DOCS-BACKLOG F4/C1) — so there is **no doc page to fetch**. Its shape is baked here, verified against the shipped `.d.ts` (`interface CometChatSettings`):

```ts
CometChatCalls.initFromSettings({
  appId: string,
  region: string,
  credentials?: { authKey?: string },
  callsSDK?: { adminHost?: string | null, clientHost?: string | null, host?: string | null,
               disableSdkIdentification?: boolean | null },
  chatSDK?: Record<string, unknown>,
  uiKit?: Record<string, unknown>,
})
```

Pass it **INLINE** — no physical `cometchat-settings.json` file is required. It returns a **Result object**, not a rejection:

```ts
{ success: false, error: { name: "VALIDATION_ERROR", message: string, timestamp: number } }
| { success: true, error: null }
```

Branch on `.success`. The publicly documented `CometChatCalls.init({ appId, region })` is the **FALLBACK only** (a non-skills / doc-following context) and returns the same Result shape.

## 1:1 RINGING — the Chat SDK half

Ringing is signaled by the **Chat SDK** (`@cometchat/chat-sdk-react-native@4`); the Calls SDK only carries media. Fetch `/calls/react-native/ringing` **directly** for the current signatures of:

- `CometChat.initiateCall(...)` — start the ring
- `CometChat.addCallListener(UNIQUE_ID, new CometChat.CallListener({ onIncomingCallReceived, onOutgoingCallAccepted, onOutgoingCallRejected, onIncomingCallCancelled }))`
- `CometChat.acceptCall(sessionId)` / `CometChat.rejectCall(sessionId, status)`
- `CometChat.removeCallListener(UNIQUE_ID)` — teardown

Then hand off to the media half: `CometChatCalls.generateToken(acceptedCall.getSessionId())` → render `<CometChatCalls.Component>`. **Two teardowns are required** — the Chat-SDK call listener AND the Calls-SDK event listeners + `leaveSession()`.

> **Sharing the session (SDK-verified, `[not in the doc]`).** To reuse the Chat SDK login for the Calls SDK, pass the Chat user's auth token to `CometChatCalls.loginWithAuthToken(...)`. The token is a **method on the User object** — `getLoggedinUser().getAuthToken()`. **There is NO top-level `CometChat.getUserAuthToken()` on the RN Chat SDK** (only `getLoggedinUser(): Promise<User|null>`); the `getUserAuthToken` name belongs to the *Calls* SDK. The `/calls/react-native/migration-guide-v5` **v4 tab shows `CometChat.getUserAuthToken()` — that is WRONG for RN** (DOCS-BACKLOG). Read from the shipped `@cometchat/chat-sdk-react-native` `.d.ts`: `getLoggedinUser` + `User.getAuthToken()`.
> ```ts
> const user = await CometChat.getLoggedinUser();
> if (user) await CometChatCalls.loginWithAuthToken(user.getAuthToken());
> ```

> **Two-client testing note.** Ringing cannot be verified from one client: it needs **two logged-in users on separate devices/simulators**. Two instances of the same build on one simulator share a session and will not ring each other. A single-client run proves the OUTGOING half only — report it that way rather than calling ringing verified.

## BACKGROUND RINGING — the half that is NOT in the ringing page

`/calls/react-native/ringing` gets you a call that rings **only while the callee's app is open**:
`onIncomingCallReceived` arrives over the Chat SDK's websocket, and a backgrounded or killed app has
no socket. Nothing errors — the callee simply never learns they were called, and the caller's call
times out (default 45s, `initiateCall(call, timeout)`).

Ringing a CLOSED app is a separate, native build. Fetch `/calls/react-native/voip-calling` for it:

- **iOS** — Push Notifications + Background Modes → **Voice over IP** capability; a **VoIP Services
  certificate** (`.p12`) uploaded to Dashboard → Notifications → Push Notifications; a native
  **PushKit + CallKit** module (`PKPushRegistry` → `CXProvider.reportNewIncomingCall`) that hands the
  answer/end actions back to JS.
- **Android** — Firebase Cloud Messaging + the server key in the dashboard; a self-managed
  **`ConnectionService`** registered in the manifest with `BIND_TELECOM_CONNECTION_SERVICE`, plus
  `MANAGE_OWN_CALLS` and `READ_PHONE_STATE`.
- **Both** — register the device token with `CometChat.registerTokenForPushNotification(token, { voip: true })`
  on iOS / without the flag on Android; on answer, `CometChat.acceptCall(sessionId)` →
  `CometChatCalls.generateToken(sessionId)` → render the Component, exactly as in the foreground flow.

**Do not improvise the native module** — follow the doc. If the pack's `cometchat-react-native-push`
skill is installed, use it for the token registration and FCM/APNs half; this page is the calls-specific
CallKit/ConnectionService layer it points at.

> **Not verifiable here.** VoIP push needs a real device, real certificates and the app backgrounded —
> it cannot be smoke-tested, CI-tested, or tested on an iOS simulator. Treat any "ringing works" claim
> without device evidence as unproven.

## Cross-platform trap

The web skill (`cometchat-js-v5-sdk`) is NOT a source of truth for React Native. Web has `joinSession(token, settings, containerEl)`, screen-share publishing, virtual backgrounds and device enumeration; **React Native has none of those**. When a web doc page and this map disagree, this map wins — and the catalog decides what exists.
