---
name: cometchat-react-native-placement
description: "Where the CometChat React Native UI Kit v5 surfaces go in a real app — one screen per route on a stack navigator, tab-based layouts, growing from the core surface to the full app, and embedding chat in an existing screen. Triggers: add a chat tab React Native, chat screen navigation RN, react-navigation CometChat, embed chat in my RN app, full chat app layout."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0; @react-navigation/native ^7"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native placement navigation layout tabs screens"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + catalog `rn-v5.json`.
> Docs: `/ui-kit/react-native/react-native-conversation` · `react-native-tab-based-chat` ·
> `expo-tab-based-chat`. Fetch props via `core/references/docs-map.md`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "add a chat tab" · "put chat on its own screen" · "chat inside my existing app"
- "build the whole chat app" · "how do I navigate from the list to a conversation"

## Prerequisites & install

Navigation is **not** bundled. The documented stack:

```bash
npm install @react-navigation/native @react-navigation/native-stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
```
⚠️ **Align these to YOUR React Native version — do not take the latest.** The UI Kit declares its peers
as `"*"`, so nothing constrains them for you. `react-native-screens` 4.x / `safe-area-context` 5.x use
Fabric codegen that RN 0.77's `@react-native/codegen` cannot parse; Metro then fails with
`Unknown prop type for "moduleId"` / `"onFinishTransitioning"` — an error naming a native codegen file,
never CometChat. Run `npx react-native doctor`, or match a known-good set for your RN
(on **0.77**: `gesture-handler@2.32.0` + `screens@4.4.0` + `safe-area-context@4.14.0`).

## The rule that governs every layout: one screen per route

**This is the single biggest difference from the web UI Kit.** React places a list and a message pane
side by side and toggles side panels with state. On a phone that is wrong:

- each surface is its **own screen** on a stack navigator
- navigation is `navigation.navigate(...)`, not conditional rendering
- **back is the hardware/gesture back button** — the OS provides it; do not hand-roll one
- there are **no side panels**. Search, thread and details are screens you push.

Conditional rendering (`{selected ? <Chat/> : <List/>}`) appears in the simplest docs recipe and is
fine for a single-screen demo, but it breaks the Android back button and loses navigation state.
Anything beyond a demo uses the navigator.

## Provider chain vs navigator — order matters

Providers wrap the navigator, not the other way round. `GestureHandlerRootView` stays outermost:

```tsx
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { NavigationContainer } from "@react-navigation/native";
import {
  CometChatI18nProvider, CometChatThemeProvider,
} from "@cometchat/chat-uikit-react-native";

export const Root = ({ children }: { children: React.ReactNode }) => (
  <GestureHandlerRootView style={{ flex: 1 }}>
    <SafeAreaProvider>
      <CometChatI18nProvider>
        <CometChatThemeProvider>
          <NavigationContainer>{children}</NavigationContainer>
        </CometChatThemeProvider>
      </CometChatI18nProvider>
    </SafeAreaProvider>
  </GestureHandlerRootView>
);
```

Putting `NavigationContainer` outside the providers means screens mount without a theme and the kit
falls back to defaults.

## Placement 1 — chat on its own screen (the default)

Two routes: the list, and the message pane. This is what an unscoped "add chat" should produce.

```tsx
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { CometChatConversations } from "@cometchat/chat-uikit-react-native";

const Stack = createNativeStackNavigator();

const ConversationsScreen = () => <CometChatConversations />;
const MessagesScreen = () => null; // header + list + composer — see `core`

export const ChatStack = () => (
  <Stack.Navigator>
    <Stack.Screen name="Conversations" component={ConversationsScreen} />
    <Stack.Screen name="Messages" component={MessagesScreen} options={{ headerShown: false }} />
  </Stack.Navigator>
);
```

`headerShown: false` on the message screen because `CometChatMessageHeader` **is** the header —
leaving the native header on gives you two stacked headers.

The list screen navigates on `onItemPress`; the message screen reads `user`/`group` from route params,
sets `showBackButton` (it defaults to `false` on RN) and wires `onBack` to `navigation.goBack()`.

## Placement 2 — a chat tab in an existing app

Chat becomes one tab beside your own screens. The bottom-tab navigator holds the tabs; a stack sits
**above** it so the message screen covers the tab bar when a conversation opens.

```tsx
<Stack.Navigator>
  <Stack.Screen name="Tabs" component={TabNavigator} options={{ headerShown: false }} />
  <Stack.Screen name="Messages" component={MessagesScreen} options={{ headerShown: false }} />
</Stack.Navigator>;
```

If `Messages` lives *inside* the tab navigator instead, the tab bar stays visible over the composer —
the classic "keyboard and tab bar fighting" bug.

## Placement 3 — grow to the full app

Add tabs for the other directories as they are asked for, each its own screen:
`CometChatConversations` (Chats) · `CometChatUsers` (Users) · `CometChatGroups` (Groups) ·
`CometChatCallLogs` (Calls). Push, don't panel:

| Surface | How it appears |
|---|---|
| thread replies | push a screen with `CometChatThreadHeader` |
| search | push a screen with `CometChatSearch`, wire `onBack` |
| group members | push a screen with `CometChatGroupMembers` |
| user/group details | **you build this** — kit v5 ships no details component (SDK fallback, see `core/references/docs-map.md`) |

`CometChatIncomingCall` is the exception: mount it **once above the navigator** so a call can arrive
on any screen.

## Placement 4 — embed in an existing screen
Chat as part of a screen rather than the whole of it. The container must still be `flex: 1` with
`minHeight: 0`; a fixed height breaks when the keyboard opens.

## Sizing and the keyboard
Every ancestor of a kit component is `flex: 1`. A scrolling column also needs `minHeight: 0`. Verify
with the keyboard **open** — the composer must stay visible, which a simulator can mislead you about.

## Common pitfalls
1. **Two headers** — `headerShown: false` on any screen using `CometChatMessageHeader`.
2. **Message screen inside the tab navigator** — tab bar overlaps the composer.
3. **Side panels ported from web** — push a screen instead.
4. **`NavigationContainer` outside the providers** — screens mount unthemed.
5. **Hand-rolled back buttons** — use the navigator's; wire `onBack` to `navigation.goBack()`.
6. **`CometChatIncomingCall` inside one screen** — calls then only arrive on that screen.

## Verify it works
- Every emitted component appears in `catalogs/rn-v5.json`.
- `npm run verify:fences:rn-v5` is green.
- On device: hardware back returns from the message screen; opening search/thread and pressing back
  returns cleanly; the composer survives the keyboard; a call arrives while on any tab.
