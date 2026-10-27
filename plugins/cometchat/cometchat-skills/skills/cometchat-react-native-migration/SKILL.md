---
name: cometchat-react-native-migration
description: "Migrate a React Native app from CometChat UI Kit v4 to v5 — the 16 removed components, what replaces each, the composite-to-modular rewrite, and the theming change from setter objects to a provider. Triggers: upgrade CometChat React Native v4 to v5, CometChatConversationsWithMessages removed, migrate RN chat uikit, CometChatDetails not found, v4 to v5 breaking changes."
license: "MIT"
compatibility: "migrating @cometchat/chat-uikit-react-native ^4 → ^5.4.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native migration upgrade v4 v5 breaking-changes"
---

> **Ground truth:** the public-export diff between kit v4 and `@cometchat/chat-uikit-react-native@5.4.0`,
> verified against `catalogs/rn-v5.json` (216 symbols) — every removal below is confirmed absent, not
> assumed. Docs: `/ui-kit/react-native/upgrading-from-v4` · `property-changes`.

## Companion skills (read first)
- `cometchat-react-native-core` — the v5 install, provider chain and ordering you are migrating **to**.

## Use this skill when
- "upgrade our chat from v4 to v5" · "`CometChatConversationsWithMessages` is gone" · "`CometChatDetails` not found"

## Prerequisites & install
v5 changes the peer set as well as the API — reinstall from `core`'s list rather than bumping one
package.

## What actually changed: composites became parts

v4 shipped end-to-end components. One tag gave you a list, a message view, details and threads. v5
removes them so each piece is customizable — which is better, and is also a **rewrite of your chat
screen**, not a version bump. Budget accordingly.

## 16 components removed — each verified absent from the v5 catalog

### Composites → stitch the parts yourself
| v4 | v5 |
|---|---|
| `CometChatConversationsWithMessages` | `CometChatConversations` + a message screen |
| `CometChatUsersWithMessages` | `CometChatUsers` + a message screen |
| `CometChatGroupsWithMessages` | `CometChatGroups` + a message screen |
| `CometChatMessages` | `CometChatMessageHeader` + `CometChatMessageList` + `CometChatMessageComposer` |
| `CometChatThreadedMessages` | `CometChatThreadHeader` on its own screen |

The message screen is three components in a `flex: 1` container — see `core`. Navigation between list
and pane is `placement`.

### Detail & management screens → **no replacement component**
`CometChatDetails` · `CometChatContacts` · `CometChatAddMembers` · `CometChatBannedMembers` ·
`CometChatTransferOwnership` · `CometChatUserMemberWrapper`

> ⚠️ **This is the migration's real cost.** v5 ships nothing equivalent. You build these screens on
> the SDK:
>
> | Screen | SDK |
> |---|---|
> | user / group details | `CometChat.getUser` · `getGroup` · `updateGroup` |
> | add members | `addMembersToGroup` |
> | **banned members** | `BannedMembersRequestBuilder` · `unbanGroupMember` |
> | transfer ownership | `transferGroupOwnership` |
>
> `CometChatGroupMembers` lists **active** members only. If your v4 app could ban, it could also show
> and unban — keep that pair, or you ship a one-way door.
>
> Do not invent a layout: the official sample app has real implementations —
> `github.com/cometchat/cometchat-uikit-react-native/tree/v5/examples/SampleApp`. Those are sample-app
> **directory paths**, never imports.

### Call-log detail screens → list only
`CometChatCallLogDetails` · `CometChatCallLogHistory` · `CometChatCallLogParticipants` ·
`CometChatCallLogRecordings` · `CometChatCallLogsWithDetails` are gone. `CometChatCallLogs` (the list)
remains; details come from `CometChatCalls.CallLogRequestBuilder` in the **calls** SDK.

## Theming: setter objects → provider

```diff
- let myTheme = new CometChatTheme({});
- myTheme.palette.setMode("dark");
+ <CometChatThemeProvider theme={{ mode: "dark" }}>
```

`CometChatContext` / `CometChatProvider` are gone. Read the active theme with `useTheme()`.
Details in `customization`.

## Migration order that avoids a broken middle
1. Upgrade the packages and the peer set; get it **building** before touching UI.
2. Replace composites with the three-part message screen (`core`).
3. Add navigation so each surface is its own screen (`placement`).
4. Rebuild the detail/management screens on the SDK — the longest step; scope it explicitly.
5. Move theming to the provider (`customization`).
6. Re-check calls and push on real devices; the native layer changed too.

## Common pitfalls
1. **Treating it as a version bump** — the chat screen is rewritten.
2. **Looking for a v5 details component** — there isn't one.
3. **Dropping banned-members** because there is no component — you lose the unban path.
4. **Porting v4 theming setters** — replaced by the provider.
5. **Keeping v4's single-screen conditional rendering** — v5 apps want a navigator.
6. **Skipping the device pass** — peers and native config changed.

## Verify it works
- No removed symbol appears anywhere: grep for `WithMessages`, `CometChatDetails`, `CometChatMessages`.
- Every emitted symbol is in `catalogs/rn-v5.json`.
- `npm run verify:fences:rn-v5` is green.
- On device: every v4 flow still exists — including viewing and unbanning banned members.
