---
name: cometchat-react-native-sdk
description: "The headless CometChat Chat SDK for React Native — a method → contract map for the fallback path, plus init/login ordering and listener lifecycle. Use when the UI Kit has no component for what you need, or when building a fully custom chat UI. Triggers: CometChat SDK React Native, headless chat RN, custom chat UI React Native, sendMessage React Native, CometChat listener leak, banned members RN, change my avatar, update my profile, update user details React Native, log the user out."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-sdk-react-native ^4.0.28"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native sdk headless methods listeners fallback"
---

> **Ground truth:** `@cometchat/chat-sdk-react-native@4` + catalog `rn-sdk-v4.json` (317 symbols).
> Signatures in `references/method-map.md` are verbatim from the installed `.d.ts`, not from prose.
> Docs: `/sdk/react-native/llms-react-native-v4.md` (scoped index).

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- **the UI Kit has no component** for what you need — the common case, see below
- "build my own chat UI" · "just give me the data layer" · "sendMessage in React Native"
- "duplicate messages" · "listener leak" · "how do I page through history"

## Prerequisites & install
The SDK ships **under** the UI Kit — if `core` is installed, so is this. A headless-only app
installs it alone:

```bash
npm install @cometchat/chat-sdk-react-native@4 @react-native-async-storage/async-storage@^2.1.2
```

⚠️ Not `@cometchat/chat-sdk-javascript` — that is the web package.

## The rule: UI Kit first, SDK as fallback

For any feature, check whether the UI Kit has a component (`components` skill + the catalog).
**If it does, use it.** Reach for the SDK only when it does not.

On React Native that fallback path is **not rare**. Kit v5 removed the detail and management
screens, so these have no component at all and are pure SDK work:

| Need | Why there is no component | Map section |
|---|---|---|
| user / group details | `CometChatDetails` removed in v5 | Users & groups |
| add members | `CometChatAddMembers` removed | Users & groups |
| **view / unban banned members** | **no UI surface exists at all** | Users & groups |
| transfer ownership | `CometChatTransferOwnership` removed | Users & groups |
| call log detail | only the list ships | Calls |

## The maps — page-wise first

**`references/page-map.md`** — the primary index, **page-wise like the JavaScript SDK repo**:
intent → the docs page → the methods that page demonstrates → the contract facts the RN page
does not carry. 37 pages, derived from the live docs so it cannot drift. Start here.

**`references/method-map.md`** — the per-method companion for when you already know the method
and need its exact signature, return type and constraints. 80 methods, 127/127 accounted for.

Both open with the same **fallback ladder**, and it matters: these cover most of the SDK, not
all of it, so **"not listed" never means "does not exist."** Rung 2 is the catalog — that, not
a map, is the existence authority.

**Load `page-map.md` for any SDK question.** It answers, per method: signature, what it resolves to, what it
rejects with, prerequisites, and what it will refuse to do. That last one matters most — it records
**negative facts** a docs page cannot express by omission, e.g. *there is no `sendCardMessage()`*,
which an agent would otherwise invent by symmetry with the three send methods that do exist.

Each row is marked `D` (backed by the RN docs) or `T` (recovered from the `.d.ts` because the RN
page is thin — **RN-G15**). Do not present a `T` row as documented; it is correct, and the docs gap
is real.

## Ordering — the invariant

Init (`initFromSettings`) must resolve before `login()`. `login()` must resolve before you fetch or
send. Anything else fails quietly rather than throwing.

```tsx
import { CometChat } from "@cometchat/chat-sdk-react-native";

// DEFAULT via skills: the ai-agent / telemetry-attributed init — persists integrationSource="ai-agent"
// (RULES §Ordering), the SDK sibling of the UI Kit's initFromSettings. Web/JS settings-OBJECT form,
// NOT the classic AppSettingsBuilder + init(APP_ID, settings). initFromSettings is @nodoc (ai-agent-only).
await CometChat.initFromSettings({
  appId: APP_ID,
  region: REGION,
  credentials: { authKey: AUTH_KEY },                        // dev only; prod logs in with an auth token
  chatSDK: { presenceSubscription: { type: "ALL_USERS" } },  // = the old .subscribePresenceForAllUsers()
});
await CometChat.login(UID, AUTH_KEY);   // dev only; production passes an auth token

// FALLBACK only (non-skills / doc-following context) — the publicly-documented classic path:
//   const settings = new CometChat.AppSettingsBuilder()
//     .setRegion(REGION).subscribePresenceForAllUsers().autoEstablishSocketConnection(true).build();
//   await CometChat.init(APP_ID, settings);
```

⚠️ `login` is **variadic and untyped** in the `.d.ts` (`login(...args: any)`), so TypeScript will
**not** catch a wrong call. The two real shapes are `login(uid, authKey)` and `login(authToken)`.

## Listener lifecycle — the defect this skill exists to prevent

```tsx
useEffect(() => {
  const id = "chat-screen";
  CometChat.addMessageListener(id, new CometChat.MessageListener({
    onTextMessageReceived: (m) => setMessages((prev) => [...prev, m]),
  }));
  return () => CometChat.removeMessageListener(id);   // NOT optional
}, []);
```

`addMessageListener` returns **void**, not a subscription — the string id is your only handle. The
SDK holds the listener, not React, so it survives navigation and unmount. Omitting the cleanup is
the top cause of duplicate messages, and it worsens the longer the app runs.

## Fetching is always a builder
Lists are paginated: `new CometChat.XRequestBuilder().setLimit(n).build()` then `.fetchNext()`.
An empty array means the end — it does not throw. There is no bare `getMessages()`.

## Common pitfalls
1. **Dropping the listener cleanup** — duplicate messages that grow over time.
2. **Calling a bare `sendMessage()`** — everything is namespaced under `CometChat`.
3. **Inventing `sendCardMessage()`** — card messages are receive-only.
4. **`await`ing `startTyping`** — it returns void.
5. **Treating `getLoggedinUser()` returning `null` as an error** — it is the normal no-session answer. (Note the lowercase `in`.)
6. **Shipping ban without unban** — `CometChatGroupMembers` shows active members only; wire `BannedMembersRequestBuilder` + `unbanGroupMember` too.
7. **Registering a push token before `login` resolves** — it belongs to no user.

## Verify it works
- Every symbol appears in `catalogs/rn-sdk-v4.json`.
- `npm run verify:fences:rn-v5` is green.
- Every `add*Listener` has a matching `remove*Listener` on the teardown path.
- Pagination, error handling and the ban round trip are wired — not just the happy path.
