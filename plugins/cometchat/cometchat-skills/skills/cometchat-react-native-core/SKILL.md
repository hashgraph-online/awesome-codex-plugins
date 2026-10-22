---
name: cometchat-react-native-core
description: "Foundational rules for the CometChat React Native UI Kit v5 — install and the exact native peer deps, the provider chain, init → login → render ordering, the component map, and the production-ready core chat surface. Read this first for any React Native CometChat task. Triggers: add chat to my React Native app, CometChat React Native setup, Expo chat, RN chat UI kit, integrate CometChat RN, log out of chat RN, add a logout button, chat lifecycle React Native."
license: "MIT"
compatibility: "Node.js >=18; React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0; @cometchat/chat-sdk-react-native ^4.0.28; optional @cometchat/calls-sdk-react-native ^5.0.4"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native expo core rules initialization provider native"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + catalog `rn-v5.json` (216 public symbols) +
> `features.rn-v5.json`. Official docs: <https://www.cometchat.com/docs/ui-kit/react-native/overview> ·
> scoped index `…/ui-kit/react-native/llms-react-native-v5.md`. Verify every symbol against the catalog;
> fetch signatures from docs (`references/docs-map.md`); never trust memory.
>
> ⚠️ **React Native is NOT React.** Different package, different API, native views instead of DOM.
> A React UI Kit snippet will not compile here. `references/docs-map.md` ends with the verified
> React → React Native name table — read it before porting anything.

## Use this skill when
- "add chat to my React Native app" · "integrate CometChat in Expo" · "RN chat UI"
- any React Native CometChat task — it is the assumed base for every other `cometchat-react-native-*` skill

## Prerequisites & install

**One package per platform.** Never mix `@cometchat/chat-uikit-react` (web) into an RN app.

```bash
npm install @cometchat/chat-uikit-react-native@5 @cometchat/chat-sdk-react-native@4
```

Then the **native peer deps — required, not optional.** Verified against `5.4.0` + the integration pages:

```bash
npm install @react-native-clipboard/clipboard \
  react-native-gesture-handler react-native-svg react-native-video react-native-localize \
  react-native-safe-area-context @react-native-async-storage/async-storage@^2.1.2 dayjs
# Expo also needs: punycode
```

`cd ios && pod install` for bare RN. **A missing native module fails at MOUNT, not at build** — the
error names a NativeModule, not CometChat, so it reads as unrelated.

⚠️ **React Native >= 0.87:** RN removed `InteractionManager` from core and the kit (through 5.5.0)
still calls it in the composer's iOS send path, so **sending a message throws on iOS** — it builds,
typechecks and bundles clean. Fix and shim: `cometchat-react-native-troubleshooting` -> *Sending a
message throws on iOS*.


## Setup & credentials (essentials — full detail: `references/setup-credentials.md`)
1. **Detect** the project: Expo (`app.json`/`app.config.js`) or bare RN (`metro.config.js`). Reuse an existing `.cometchat/config.json` or env if present — skip re-setup.
2. **version_conflict — STOP** if `@cometchat/chat-uikit-react-native` is already in `package.json` at a non-v5 major; reconcile first, never mix majors (`RULES.md`).
3. **Credentials — OFFER the dashboard fetch FIRST** (never silently "paste it yourself" — AUDIT-039). Offer both, defaulting to fetch: **(a) dashboard fetch (recommended)** — `npx @cometchat/skills-cli@3 auth login`, pick an EXISTING app (`provision list --json`; never auto-create), `provision use --app-id <id> --json` writes `.cometchat/config.json`; **(b) manual paste** from Dashboard → Credentials (dev-only Auth Key). **Then the SKILL writes the env (§4)** — the CLI stops at the fetch; env-writing and codegen are the SKILL's job. Full flow: `references/setup-credentials.md`.
4. **Write env**: bare RN → `.env` (read via `react-native-config`); Expo → `.env` (read via `Constants.expoConfig.extra` or `process.env`). Gitignore it; never echo the Auth Key. Prod → server-minted auth token, not the Auth Key. **Nothing in a mobile bundle is secret** (IPA/APK are readable) — see `references/setup-credentials.md`.
5. **Authorize** = `initFromSettings` then `login` both resolve; auth error is almost always the wrong Region.

## Integration ordering (BAKED — invariant)

**`init()` must resolve before `login()`. `login()` must resolve before you render any component.**
Breaking it gives a blank screen, not an error.

Use **`initFromSettings`**, not the classic `init` — it persists `integrationSource="ai-agent"`
so CometChat can attribute the integration. The classic init does not (AUDIT-084), and a machine
gate enforces this.

```tsx
import { CometChatUIKit } from "@cometchat/chat-uikit-react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";

const settings: CometChat.CometChatSettings = {
  appId: APP_ID,
  region: REGION,
  credentials: { authKey: AUTH_KEY }, // dev only — production mints an auth token server-side
  chatSDK: {
    presenceSubscription: { type: "ALL_USERS" },
    autoEstablishSocketConnection: true,
  },
};

await CometChatUIKit.initFromSettings(settings);
await CometChatUIKit.login({ uid: UID });   // or ({ authToken }) in production
```

Note the shape: presence moves **into** `chatSDK.presenceSubscription.type` — it is not a
top-level field and not a builder call.

⚠️ **Two shapes that differ from React and will not compile if ported:**
- settings is a **plain object** — there is no `UIKitSettingsBuilder` export in RN
- `login` takes an **object**: `login({ uid })`, not `login(uid)`

Use an existing UID from your dashboard (the sample apps seed `cometchat-uid-1`). Never invent one.

## The provider chain (BAKED — order is load-bearing)

Outermost first. Verified against the integration + recipe pages:

```tsx
<GestureHandlerRootView style={{ flex: 1 }}>
  <SafeAreaProvider>
    <CometChatI18nProvider>
      <SafeAreaView style={{ flex: 1 }}>
        <CometChatThemeProvider>
          {/* screens */}
        </CometChatThemeProvider>
      </SafeAreaView>
    </CometChatI18nProvider>
  </SafeAreaProvider>
</GestureHandlerRootView>
```

**`GestureHandlerRootView` is outermost and must carry `flex: 1`.** Omit it and swipe / long-press
silently do nothing — no error, no warning. It is the single most common "the UI renders but nothing
responds" cause on RN.

## Sizing — flex, never viewport units

There is no `100dvh` and no CSS. The rule: **every ancestor of a kit component is `flex: 1`**, and a
scrolling column also needs `minHeight: 0`. A fixed pixel height breaks when the soft keyboard opens.
The composer must remain visible with the keyboard up — verify on a device, not only a simulator.

## Component / API map (BAKED closed list — from `catalogs/rn-v5.json`)

| Need | Component |
|---|---|
| conversation list | `CometChatConversations` |
| message pane | `CometChatMessageHeader` · `CometChatMessageList` · `CometChatMessageComposer` |
| compact composer | `CometChatCompactMessageComposer` |
| threads | `CometChatThreadHeader` |
| search | `CometChatSearch` |
| users / groups / members | `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` |
| calls | `CometChatCallButtons` · `CometChatIncomingCall` · `CometChatOutgoingCall` · `CometChatOngoingCall` · `CometChatCallLogs` |
| theming / i18n | `CometChatThemeProvider` + `useTheme()` · `CometChatI18nProvider` |
| extension chain | `ChatConfigurator` + `DataSourceDecorator` |

Anything not in `catalogs/rn-v5.json` **does not exist** — do not emit it. Notably absent in v5:
`CometChatErrorBoundary`, `CometChatDetails`, `CometChatAddMembers`, `CometChatBannedMembers`,
`CometChatTransferOwnership`, and every `*WithMessages` composite. See `references/docs-map.md`
for the SDK-fallback path for each.

## Callback names — RN uses `Press`, not `Click`

| Component | Wire these |
|---|---|
| `CometChatConversations` | `onItemPress` · `onSearchBarClicked` · `onError` |
| `CometChatMessageList` | `onThreadRepliesPress` · `onError` |
| `CometChatMessageHeader` | `showBackButton` (default `false`) + `onBack` · `onError` |
| `CometChatSearch` | `onBack` · `onConversationClicked` · `onMessageClicked` |

React's `onItemClick` / `onThreadRepliesClick` do not exist here.

> ⚠️ **On `CometChatGroupMembers`, `onError` takes NO argument** in kits up to **5.5.0** —
> `onError?: () => void`, unlike every other list. Type the handler with a parameter there and it fails
> with TS2322. Write `onError={() => …}` and show the failure with the `ErrorView` slot, which needs no
> error object. Fixed in the kit (uikit-react-native#1452); once that ships, the parameter is available
> and this note goes away.

## Golden path — the production-ready core surface

The default for an unscoped "add chat". **One screen per route on a stack navigator with a real back
button** — never two panes side by side, and never a web-style side panel.

```tsx
// ChatScreen.tsx — the message pane
import {
  CometChatMessageHeader, CometChatMessageList, CometChatMessageComposer,
} from "@cometchat/chat-uikit-react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";
import { View } from "react-native";

export const ChatScreen = ({ user, group, onBack }: {
  user?: CometChat.User; group?: CometChat.Group; onBack: () => void;
}) => (
  <View style={{ flex: 1 }}>
    {/* showBackButton defaults to FALSE on RN — without it onBack never fires */}
    <CometChatMessageHeader user={user} group={group} showBackButton onBack={onBack} />
    <CometChatMessageList user={user} group={group} />
    <CometChatMessageComposer user={user} group={group} />
  </View>
);
```

```tsx
// ConversationsScreen.tsx — the list, wired to open the pane
import { CometChatConversations, CometChatUiKitConstants } from "@cometchat/chat-uikit-react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";

export const ConversationsScreen = ({ onOpen }: {
  onOpen: (user?: CometChat.User, group?: CometChat.Group) => void;
}) => (
  <CometChatConversations
    onItemPress={(conversation: CometChat.Conversation) => {
      const isUser =
        conversation.getConversationType() ===
        CometChatUiKitConstants.ConversationTypeConstants.user;
      isUser
        ? onOpen(conversation.getConversationWith() as CometChat.User, undefined)
        : onOpen(undefined, conversation.getConversationWith() as CometChat.Group);
    }}
  />
);
```

### The core surface is FOUR things, not two

`contracts.rn-v5.json` → `core-chat-surface` mandates all four by default, and the reviewer's G1
gate fails an emit that ships fewer. A list ↔ message pane is **half the surface**:

| Capability | Component | Wire |
|---|---|---|
| conversations | `CometChatConversations` | `onItemPress` |
| messages | `CometChatMessageHeader` + `List` + `Composer` | `showBackButton` + `onBack` |
| **threaded replies** | `CometChatThreadHeader` | `onThreadRepliesPress` → push a thread screen |
| **search** | `CometChatSearch` | `showSearchBar={true}` **+** `onSearchBarClicked` → push a search screen |

On RN both are **pushed screens**, not side panels. Search is opt-out only, and must cover the
global (list) case *and* the in-chat case scoped to the open conversation.

```tsx
// message pane — thread entry point
<CometChatMessageList
  user={user}
  group={group}
  onThreadRepliesPress={(message) => openThread(message)}
/>

// conversation list — search entry point.
// showSearchBar defaults to FALSE on RN (it is true on React), so the callback alone
// silently ships a surface with no search. Both props, always.
<CometChatConversations
  onItemPress={open}
  showSearchBar={true}
  onSearchBarClicked={() => openSearch()}
/>
```

The callbacks above are only the **entry points**. `openThread` and `openSearch` push screens, and
those screens are where the two mandated components actually render — emit both, or the surface
has tap targets that lead nowhere:

```tsx
// ThreadScreen — what openThread(message) pushes to.
// parentMessageId is typed `string` on the list and `string | number` on the composer,
// so the list needs .toString().
function ThreadScreen({ route, navigation }) {
  const { parentMessage, user, group } = route.params;
  return (
    <View style={{ flex: 1, minHeight: 0 }}>
      <CometChatThreadHeader parentMessage={parentMessage} />
      <CometChatMessageList
        user={user}
        group={group}
        parentMessageId={parentMessage.getId().toString()}
      />
      <CometChatMessageComposer
        user={user}
        group={group}
        parentMessageId={parentMessage.getId()}
      />
    </View>
  );
}
```

```tsx
// SearchScreen — what openSearch() pushes to.
// Omit uid/guid for the GLOBAL case (from the conversation list); pass one to scope the
// search to the open conversation. Both cases are mandated — one screen serves both.
function SearchScreen({ route, navigation }) {
  const { user, group } = route.params ?? {};
  return (
    <CometChatSearch
      onBack={() => navigation.goBack()}
      uid={user?.getUid()}
      guid={group?.getGuid()}
      onConversationClicked={(conversation) => navigation.navigate("Messages", { conversation })}
      onMessageClicked={(message) => navigation.navigate("Messages", { message })}
      onError={(e) => console.error(e)}
    />
  );
}
```

> **Search:** `CometChatSearch` is documented at `{DOCS_BASE}/ui-kit/react-native/search` (fetch it
> via `references/docs-map.md`); wire `onConversationClicked` / `onMessageClicked` and its `onBack`.
> (Formerly tracked as gap RN-G1 — the page has since been published.)

**Every affordance that is visible by default is wired or hidden.** A tap target that does nothing is
a defect, and so is an opened surface with no way back — if you open search or a thread, wire its
`onBack` in the same edit.

## Deep references (load only when the task needs them)
- `references/docs-map.md` — intent → the exact docs page; the SDK-fallback table; the React→RN name table. **Read before porting any React snippet.**
- `references/component-props.md` — baked props + **PascalCase view slots** per drop-in, and the defaults that differ from React (`showSearchBar` is `false` here). **Read before placing custom UI** — it goes in a slot, never as a sibling.
- `references/anti-patterns.md` — the 13 failures that actually break an RN integration, each with why its error names the wrong thing.
- `references/lifecycle.md` — `initFromSettings` → login → render, and the promise-cached boot guard (a boolean flag does not work).
- `references/layout.md` — the four sizing invariants the `core-chat-surface` contract gates on.
- `references/dependencies.md` — the exact peer set + the native config that is not optional (Podfile modular headers, gesture-handler import order).
- `references/setup-credentials.md` — dev vs production auth, and why nothing in a mobile bundle is secret.

## Common pitfalls
1. **Missing `GestureHandlerRootView`** — gestures silently dead. Outermost, `flex: 1`.
2. **Rendering before `login()` resolves** — blank screen, no error.
3. **Porting React code** — `UIKitSettingsBuilder`, `login(uid)`, `onItemClick`, CSS, `document.*`: none exist here.
4. **Fixed heights** — breaks on keyboard open. Use `flex: 1` + `minHeight: 0`.
5. **Shipping the Auth Key** — dev only; production mints an auth token server-side.

## Verify it works
- Every emitted symbol appears in `catalogs/rn-v5.json`.
- Code compiles against the pinned kit: `npm run verify:fences:rn-v5`.
- Oracles agree with the kit and docs: `npm run verify:sync:rn-v5`.
- **`tsc --noEmit` in the APP is not clean, and that is not the app's bug.** The kit ships raw
  `src/*.tsx` as its `main`/`module` with no built declarations, so TypeScript follows the import and
  typechecks the kit itself (`NodeJS` namespace, implicit `any`, `isolatedModules` re-exports,
  `User | null`, and on RN 0.87 a `RefObject<TextInputType>` mismatch). Gate on the **Metro bundle**
  instead — `npx react-native bundle --platform ios|android --dev false --entry-file index.js
  --bundle-output /dev/null` — and if you want a typecheck, filter the kit's own files out of the
  output. Never "fix" node_modules, and never report the app as failing typecheck because of them.
- **Getting the app to actually RUN on a shared machine.** React Native asks for Metro on port 8081
  and takes whatever answers: another project's packager serves a foreign bundle, and the app dies
  with `Invariant Violation: TurboModuleRegistry.getEnforcing('PlatformConstants')` — a version
  mismatch that reads like a missing native module. iOS: point the app at your packager with
  `xcrun simctl spawn <udid> defaults write <bundle-id> RCT_jsLocation "localhost:<port>"`
  (`RCT_METRO_PORT` does not change the runtime URL). Android: `adb reverse tcp:8081 tcp:<port>`, and
  when that silently does nothing — it does on some emulators — embed the bundle instead:
  `npx react-native bundle --platform android --dev false --entry-file index.js --bundle-output
  android/app/src/main/assets/index.android.bundle --assets-dest android/app/src/main/res`, then
  `run-android`. Remove that file before going back to Fast Refresh.
- On a device: chat fills the screen, the composer survives the keyboard, back works, gestures respond.

## Explain what you built (REQUIRED close)
Tell the user briefly: **(1) what I wired** (3–5 bullets, NAME the files); **(2) decisions & why**, flagging dev-only AS dev-only (the **Auth Key** is dev-only → server-minted auth token for production; the `<uid>` you used; Expo vs bare RN path); **(3) what I did NOT touch** (additive — navigation/auth/styles intact). Then **offer these THREE options as a selectable choice and WAIT — do not auto-continue:**
- **① Add another feature** — check what's already wired; ASK which Dashboard extensions are enabled; suggest 3–4 gaps (**calls · push · AI smart replies · polls · stickers · translation · notification feed**). Never suggest reactions or mentions — they are ON by default in v5. → `cometchat-react-native-features` / `cometchat-react-native-calls` / `cometchat-react-native-push`.
- **② Customize theming** — ask for brand color / light-dark → `cometchat-react-native-customization`.
- **③ Test it manually** — hand it back so they run it on a device.
