<!-- family-agnostic: per-platform-by-design — this reference IS the per-platform Sendbird inventory + target-family table; one row per platform by design. -->
# Sendbird inventory — what to find, and where it goes

Search case-insensitively. Skip `node_modules/`, `Pods/`, `build/`, `.dart_tool/`, `.gradle/` and `.git/`. A package hit tells you Sendbird is present. The **import/API hits** tell you *what the app does with it*, and each one becomes a ledger row (`file:line → purpose`). The names below are the common ones, not a closed list: any identifier starting with `Sendbird`/`SendBird`/`SB` imported from a Sendbird package counts.

## Target family (where each platform lands)
| App platform (detect `framework`) | Sendbird packages you'll see | CometChat family (`peers.yaml`) | UIKit mode → | SDK mode (own UI) → |
|---|---|---|---|---|
| React / Next / Vite / CRA / Astro / React Router | `@sendbird/uikit-react`, `sendbird-uikit` (v2), `@sendbird/chat`, `sendbird` (v3) | `react-v7` | `cometchat-react-v7-core` + `-components`/`-placement` | the core's SDK fallback (`@cometchat/chat-sdk-javascript`, docs-map → SDK docs) |
| Angular | `@sendbird/chat`, `sendbird` (no official Angular UIKit — usually SDK mode) | `angular-v5` | `cometchat-angular-v5-core` | the core's SDK fallback (JS Chat SDK) |
| React Native / Expo | `@sendbird/uikit-react-native`, `@sendbird/uikit-react-native-foundation`, `@sendbird/chat`, `@sendbird/calls-react-native` | `react-native` | `cometchat-react-native-core` | `cometchat-react-native-sdk` |
| iOS (Swift) | SPM `sendbird-chat-sdk-ios` / `sendbird-uikit-ios` / `sendbird-swiftui-ios`; pods `SendbirdChatSDK`, `SendBirdUIKit`, `SendBirdSDK` (v3), `SendBirdCalls` | `ios` | `cometchat-ios-core` (UIKit; host SwiftUI screens via a representable) | the iOS core's SDK fallback (`CometChatSDK`) |
| Android | `com.sendbird.sdk:sendbird-chat`, `com.sendbird.sdk:uikit`, `com.sendbird.sdk:uikit-compose`, `com.sendbird.sdk:sendbird-calls`, the `repo.sendbird.com` Maven repo | `android-v6` (cohort from `android_variant`: Compose → `compose-*`, Views → `kotlin-*`) | `cometchat-android-v6-core` | `cometchat-android-v5-sdk` |
| Flutter | `sendbird_uikit`, `sendbird_chat_sdk`, `sendbird_sdk` (v3) | `flutter-v6` | `cometchat-flutter-v6-core` | the Flutter core's SDK fallback (`cometchat_sdk`, re-exported by the kit) |
| Calls only (no chat) | `sendbird-calls`, `@sendbird/calls-react-native`, `SendBirdCalls`, `com.sendbird.sdk:sendbird-calls` | the matching headless calls peer (`js-calls`, `react-native-calls`, `ios-calls`, `android-calls`, `flutter-calls`) | — | `cometchat-js-v5-sdk` / `cometchat-react-native-v5-sdk` / `cometchat-ios-v5-sdk` / `cometchat-android-v5-calls-sdk` / `cometchat-flutter-v5-sdk` |
| Server (Node, Python, Go, Java, Ruby, PHP…) | HTTP to `api-<APP_ID>.sendbird.com/v3/…` with an `Api-Token` header; `sendbird-platform-sdk*` | — (REST, no UI Kit) | — | CometChat REST (`/rest-api/…`) |

A platform that isn't in this table (Vue, Svelte, Unity, .NET MAUI, Unreal…) has no family in this pack → STOP (2): report only.

### React Native is a native platform for the build, not a web one
The migration is not done when Metro bundles: `cd ios && pod install` (the kit's Podfile needs the
`modular_headers` lines the family `-core` lists, or `pod install` itself fails), then BUILD **and
RUN** both platforms. Three failures never appear in CI — only when a person uses the app:

| Trap | What you see |
|---|---|
| React Native >= 0.87 on iOS | the kit's composer calls `InteractionManager`, removed from RN core in 0.87 — tapping send throws (`InteractionManager has been removed from react-native core`); Android is unaffected. Shim: the family `-troubleshooting` |
| a missing native peer | fails at MOUNT, and the error names the peer (`gesture-handler`, `svg`, `video`), never CometChat |
| `tsc --noEmit` | reports errors from inside the kit's own shipped source (it ships raw `src/*.tsx`), so gate on the Metro bundle — see the family `-core` -> Verify it works, which also carries the run recipe for a machine where port 8081 is taken |

## Grep signals
**Manifests**: `package.json`, `pubspec.yaml`, `build.gradle(.kts)`, `settings.gradle(.kts)`, `gradle/libs.versions.toml`, `Podfile`, `Package.swift`, `*.xcodeproj/project.pbxproj`, `Package.resolved`, `requirements.txt`, `go.mod`, `Gemfile` and `composer.json` → `sendbird`.

**Init / auth**:
- v4 SDK: `SendbirdChat.init`, `.connect(`, `.disconnect(`, `authToken`/`accessToken`/`sessionToken`, `SessionHandler` (token refresh).
- v3 SDK: `new SendBird(`, `SendBird.getInstance()`.
- iOS: `SendbirdUI.initialize`, `SBUGlobals.currentUser`.
- Android: `SendbirdUIKit.init`, `SendbirdUIKitAdapter`.

**Providers / screens (UIKit)**:
- React:
  - `SendbirdProvider`, `App` (from `@sendbird/uikit-react/App`).
  - `GroupChannelList`, `GroupChannel`, `ChannelList`, `Channel`, `ChannelSettings`.
  - `Thread`, `MessageSearch`, `CreateChannel`, `OpenChannel`, `OpenChannelSettings`, `EditUserProfile`.
  - `useSendbirdStateContext`, `sendbirdSelectors`.
  - CSS `@sendbird/uikit-react/dist/index.css`.
- React Native: `SendbirdUIKitContainer`, `createGroupChannelListFragment`, `createGroupChannelFragment`, `createGroupChannelCreateFragment`, `createGroupChannelSettingsFragment`, `useSendbirdChat`, `useConnection`, `platformServices`.
- iOS: `SBUGroupChannelListViewController`, `SBUGroupChannelViewController`, `SBUOpenChannelViewController`, `SBUCreateChannelViewController`, `SBUMessageThreadViewController`, `SBUTheme`, `SBUStringSet`; SwiftUI `GroupChannelListView`, `GroupChannelView`.
- Android: `ChannelListActivity`, `ChannelActivity`, `ChannelListFragment`, `ChannelFragment`, `OpenChannelFragment`, `MessageThreadFragment`, `SendbirdUIKit.setDefaultThemeMode`; Compose `ChannelListScreen`, `ChannelScreen`, `SendbirdUikitCompose`.
- Flutter: `SendbirdUIKit.init`, `SBUGroupChannelListScreen`, `SBUGroupChannelScreen`, `SBUTheme`.

**Channels**:
- `GroupChannel`, `OpenChannel`, `FeedChannel`.
- Creation: `createChannel`, `createChannelWithUserIds`, `GroupChannelCreateParams`, `isDistinct`, `isSuper`, `isPublic`, `isBroadcast`, `isEphemeral`, `customType`.
- Queries: `GroupChannelListQuery`, `createMyGroupChannelListQuery`, `GroupChannelCollection`.

**Messages**:
- Send: `sendUserMessage`, `sendFileMessage`, `sendFileMessages`, `sendScheduledMessage`/`createScheduledUserMessage`.
- Edit/delete: `updateUserMessage`, `deleteMessage`.
- Load: `PreviousMessageListQuery`, `getMessagesByTimestamp`, `MessageCollection`.
- Threads and replies: `parentMessageId`, `ThreadInfo`, `ReplyType`.
- Flags: `copyUserMessage`/`copyFileMessage`, `pinMessage`, `markAsRead`, `markAsDelivered`, `markAsUnread`.
- Extras: `addReaction`, `mentionedUsers`/`MentionType`, `translateUserMessage`/`translationTargetLanguages`, `ogMetaData`, `metaArrays`, `message.data`/`customType`.

**Events**: `GroupChannelHandler`, `OpenChannelHandler`, `ChannelHandler` (v3), `ConnectionHandler`, `UserEventHandler`, `addGroupChannelHandler`/`addChannelHandler`, `onMessageReceived`, `onTypingStatusUpdated`, `onReadStatus`/`onUnreadMemberStatusUpdated`, `onDeliveryReceiptUpdated`, `onReactionUpdated`.

**Users / moderation**:
- Users: `blockUser`, `unblockUser`, `ApplicationUserListQuery`, `updateCurrentUserInfo`, `UserEventHandler`.
- Channel moderation: `banUser`, `muteUser`, `freeze`, `addOperators`, `report` (`reportUser`/`reportMessage`/`reportChannel`).
- Channel data: `createMetaData`, `createMetaCounters`.
- Membership: `hide`/`unhide`, `invite`/`acceptInvitation`/`declineInvitation`, `setMyPushTriggerOption`, `setDoNotDisturb`, `setSnoozePeriod`, `setCountPreference`.

**Push**: `registerFCMPushTokenForCurrentUser`, `registerAPNSPushTokenForCurrentUser`, `registerPushToken`, `SendbirdPushHelper`, `SendbirdPushHandler`, `unregisterPushToken*`. Also check the push message payload parsing: a `sendbird` key in the notification data.

**Other products**:
- Calls: `SendBirdCall`, `SendbirdCall`, `DirectCall`, `dial(`, `Room`/`RoomType`.
- Desk: `sendbird-desk`, `SendBirdDesk`, `Ticket`.
- Live: `@sendbird/live`.
- AI chatbot: `bot`/`ai_agent` channel types, `AIChatBot`, `@sendbird/chat-ai-widget`.
- Business Messaging / Notifications: `FeedChannel`, `NotificationCollection`, message templates.

**Server**: `api-*.sendbird.com`, `Api-Token`, `/v3/users/*/token` (session tokens), `/v3/group_channels`, `/v3/open_channels`, and webhook handlers that verify `x-sendbird-signature`.

**Env / config**: `SENDBIRD_APP_ID`, `VITE_SENDBIRD_*`, `NEXT_PUBLIC_SENDBIRD_*`, `EXPO_PUBLIC_SENDBIRD_*`, `SENDBIRD_API_TOKEN`, `SendbirdAppId` in plists/`local.properties`/`--dart-define`, and CI secrets named `SENDBIRD_*`.

**Tests / mocks**: `jest.mock('@sendbird/…')`, fake `SendbirdChat`, and fixtures containing channel URLs.
